import { PublicKey, SystemProgram } from '@solana/web3.js';
import { getProgram, getPhantom, leveragedPositionPda, BN } from './client';

export interface OpenParams {
	wallet: string;
	asset: 'SOL' | 'BTC' | 'ETH';
	direction: 'LONG' | 'SHORT';
	collateralUsd: number;
	leverage: number;
}

const ASSET_VARIANT: Record<string, { sol?: {}; btc?: {}; eth?: {} }> = {
	SOL: { sol: {} },
	BTC: { btc: {} },
	ETH: { eth: {} },
};
const DIRECTION_VARIANT: Record<string, { long?: {}; short?: {} }> = {
	LONG: { long: {} },
	SHORT: { short: {} },
};

async function fetchPythPrice(asset: string): Promise<number> {
	const res = await fetch(`/api/pyth/${asset}`);
	if (!res.ok) throw new Error(`Pyth price unavailable (HTTP ${res.status})`);
	const data = await res.json();
	return data.price;
}

async function fetchSolPrice(): Promise<number> {
	return fetchPythPrice('SOL');
}

export async function openLeveragedPosition(params: OpenParams) {
	const phantom = getPhantom();
	if (phantom.publicKey.toBase58() !== params.wallet) {
		throw new Error('Connected wallet does not match');
	}
	const program = getProgram();

	const entryPrice = await fetchPythPrice(params.asset);
	const entryPriceMicro = new BN(Math.round(entryPrice * 1_000_000));

	const solPrice = await fetchSolPrice();
	const collateralSol = params.collateralUsd / solPrice;
	const collateralLamports = new BN(Math.round(collateralSol * 1_000_000_000));

	const leverageBps = Math.round(params.leverage * 100);
	const nonce = BigInt(Date.now());

	const [positionPda] = leveragedPositionPda(phantom.publicKey, nonce);

	const sig = await program.methods
		.openLeveragedPosition(
			new BN(nonce.toString()),
			ASSET_VARIANT[params.asset],
			DIRECTION_VARIANT[params.direction],
			collateralLamports,
			leverageBps,
			entryPriceMicro,
		)
		.accounts({
			position: positionPda,
			authority: phantom.publicKey,
			systemProgram: SystemProgram.programId,
		})
		.rpc();

	return {
		signature: sig,
		positionPda: positionPda.toBase58(),
		nonce: nonce.toString(),
		entryPrice,
		collateralSol,
	};
}

export async function closeLeveragedPosition(positionPda: string, exitPrice: number) {
	const phantom = getPhantom();
	const program = getProgram();

	const exitPriceMicro = new BN(Math.round(exitPrice * 1_000_000));

	const sig = await program.methods
		.closeLeveragedPosition(exitPriceMicro)
		.accounts({
			position: new PublicKey(positionPda),
			authority: phantom.publicKey,
		})
		.rpc();

	return { signature: sig };
}

export async function listOnChainPositions(wallet: string) {
	const program = getProgram();
	const walletKey = new PublicKey(wallet);
	// @ts-ignore Anchor typing for dynamic accounts
	const all = await program.account.leveragedPosition.all([
		{ memcmp: { offset: 8, bytes: walletKey.toBase58() } },
	]);
	return all.map((item: any) => {
		const acc = item.account;
		const assetRaw = Object.keys(acc.asset)[0];
		const directionRaw = Object.keys(acc.direction)[0];
		return {
			pda: item.publicKey.toBase58(),
			authority: acc.authority.toBase58(),
			nonce: acc.nonce.toString(),
			asset: assetRaw.toUpperCase(),
			direction: directionRaw.toUpperCase(),
			collateralLamports: acc.collateralLamports.toString(),
			leverageBps: Number(acc.leverageBps),
			entryPriceMicro: acc.entryPriceMicro.toString(),
			openedAt: Number(acc.openedAt),
		};
	});
}
