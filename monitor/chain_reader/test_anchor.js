// End-to-end smoke test for the Sentinel Anchor program.
// Opens a leveraged position, reads it back, closes it — using the deploy-keypair.

const fs = require('fs');
const path = require('path');
const { Connection, Keypair, PublicKey, SystemProgram } = require('@solana/web3.js');
const anchor = require('@coral-xyz/anchor');

const IDL = require('../../target/idl/sentinel.json');
const PROGRAM_ID = new PublicKey('5QiE51bSE3yqJFmRhj1CHt2NwaJpC2iodsaLDrZJDheE');
const LEVERAGED_SEED = Buffer.from('lev_pos');
const RPC = 'https://api.devnet.solana.com';

function keypairFromFile(p) {
	const raw = JSON.parse(fs.readFileSync(p, 'utf8'));
	return Keypair.fromSecretKey(Uint8Array.from(raw));
}

function leveragedPda(authority, nonce) {
	const nonceBuf = Buffer.alloc(8);
	nonceBuf.writeBigUInt64LE(BigInt(nonce), 0);
	return PublicKey.findProgramAddressSync(
		[LEVERAGED_SEED, authority.toBuffer(), nonceBuf],
		PROGRAM_ID,
	);
}

async function main() {
	const keypairPath = path.resolve(__dirname, '../../deploy-keypair.json');
	const payer = keypairFromFile(keypairPath);
	const wallet = new anchor.Wallet(payer);
	const conn = new Connection(RPC, 'confirmed');
	const provider = new anchor.AnchorProvider(conn, wallet, { commitment: 'confirmed' });
	const program = new anchor.Program(IDL, provider);

	console.log(`authority: ${payer.publicKey.toBase58()}`);
	const bal = await conn.getBalance(payer.publicKey);
	console.log(`balance: ${(bal / 1e9).toFixed(4)} SOL`);

	const nonce = Date.now();
	const [pda] = leveragedPda(payer.publicKey, nonce);
	console.log(`position PDA: ${pda.toBase58()} (nonce=${nonce})`);

	// Fetch SOL price from our FastAPI (sentinel local)
	const fetch = (url) => new Promise((resolve, reject) => {
		require('http').get(url, (res) => {
			let d = '';
			res.on('data', (c) => (d += c));
			res.on('end', () => resolve(JSON.parse(d)));
		}).on('error', reject);
	});
	const pyth = await fetch('http://127.0.0.1:8001/api/pyth/SOL');
	const solPrice = pyth.price;
	console.log(`pyth SOL: $${solPrice.toFixed(4)}`);

	const collateralUsd = 0.5 * solPrice; // 0.5 SOL worth
	const collateralLamports = new anchor.BN(Math.round(0.5 * 1e9));
	const leverageBps = 500; // 5x
	const entryPriceMicro = new anchor.BN(Math.round(solPrice * 1e6));

	console.log(`\n▶ OPEN: 5x LONG SOL, collateral 0.5 SOL (~$${collateralUsd.toFixed(2)})`);
	const openSig = await program.methods
		.openLeveragedPosition(
			new anchor.BN(nonce),
			{ sol: {} },
			{ long: {} },
			collateralLamports,
			leverageBps,
			entryPriceMicro,
		)
		.accounts({
			position: pda,
			authority: payer.publicKey,
			systemProgram: SystemProgram.programId,
		})
		.rpc();
	console.log(`  sig: ${openSig}`);

	const acc = await program.account.leveragedPosition.fetch(pda);
	console.log(`\n▶ READBACK:`);
	console.log(`  authority:  ${acc.authority.toBase58()}`);
	console.log(`  asset:      ${Object.keys(acc.asset)[0]}`);
	console.log(`  direction:  ${Object.keys(acc.direction)[0]}`);
	console.log(`  collateral: ${Number(acc.collateralLamports) / 1e9} SOL`);
	console.log(`  leverage:   ${Number(acc.leverageBps) / 100}x`);
	console.log(`  entryPrice: $${Number(acc.entryPriceMicro) / 1e6}`);
	console.log(`  openedAt:   ${new Date(Number(acc.openedAt) * 1000).toISOString()}`);

	// List via program filter
	console.log(`\n▶ LIST via program.account.leveragedPosition.all (memcmp authority):`);
	const all = await program.account.leveragedPosition.all([
		{ memcmp: { offset: 8, bytes: payer.publicKey.toBase58() } },
	]);
	console.log(`  found ${all.length} position(s) for this authority`);

	console.log(`\n▶ CLOSE at exit price $${solPrice.toFixed(4)}:`);
	const closeSig = await program.methods
		.closeLeveragedPosition(entryPriceMicro)
		.accounts({
			position: pda,
			authority: payer.publicKey,
		})
		.rpc();
	console.log(`  sig: ${closeSig}`);

	const balAfter = await conn.getBalance(payer.publicKey);
	console.log(`\n▶ balance after: ${(balAfter / 1e9).toFixed(4)} SOL (net: ${((balAfter - bal) / 1e9).toFixed(4)} SOL)`);

	// Verify account is gone
	const accAfter = await conn.getAccountInfo(pda);
	console.log(`  position account after close: ${accAfter ? 'STILL EXISTS (fail)' : 'closed (ok)'}`);
}

main().catch((e) => {
	console.error('FAIL:', e?.message || e);
	if (e?.logs) console.error(e.logs.join('\n'));
	process.exit(1);
});
