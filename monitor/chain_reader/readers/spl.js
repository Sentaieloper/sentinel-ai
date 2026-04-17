const { PublicKey } = require('@solana/web3.js');
const { TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID } = require('@solana/spl-token');

// Token mint registry. Uses mainnet mints; the same addresses are also
// whitelisted on devnet when a matching mint exists. WSOL and the devnet
// USDC mint `Gh9ZwEmdLJ8D...` are additionally accepted.
const KNOWN_TOKENS = {
	EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v: { symbol: 'USDC', decimals: 6 },
	Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr: { symbol: 'USDC-dev', decimals: 6 },
	So11111111111111111111111111111111111111112: { symbol: 'WSOL', decimals: 9 },
	mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So: { symbol: 'mSOL', decimals: 9 },
	J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn: { symbol: 'JitoSOL', decimals: 9 },
	bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1: { symbol: 'bSOL', decimals: 9 },
	BNso1VUJnh4zcfpZa6986Ea66P6TCp59hvtNJ8b1X85: { symbol: 'BNSOL', decimals: 9 },
};

async function read(connection, wallet) {
	const out = [];
	for (const programId of [TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID]) {
		const resp = await connection.getParsedTokenAccountsByOwner(wallet, { programId });
		for (const { account } of resp.value) {
			const info = account.data.parsed?.info;
			if (!info) continue;
			const mint = info.mint;
			const raw = info.tokenAmount?.uiAmount ?? 0;
			if (!raw || raw <= 0) continue;
			const meta = KNOWN_TOKENS[mint];
			if (!meta) continue; // skip unknown dust
			if (mint === 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So') continue; // handled by marinade reader
			out.push({
				id: `spl-${mint}-${wallet.toBase58()}`,
				protocol: 'Wallet',
				asset: meta.symbol,
				balance: raw,
				mint,
				riskLevel: 'Safe',
				source: 'spl',
				lastChecked: 'just now',
			});
		}
	}
	return out;
}

module.exports = { read };
