import './polyfills';
import { AnchorProvider, Program, BN } from '@coral-xyz/anchor';
import type { Idl } from '@coral-xyz/anchor';
import { Connection, PublicKey, Transaction, VersionedTransaction } from '@solana/web3.js';
import idl from './sentinel.json';

export const SENTINEL_PROGRAM_ID = new PublicKey('5QiE51bSE3yqJFmRhj1CHt2NwaJpC2iodsaLDrZJDheE');
export const LEVERAGED_SEED = new TextEncoder().encode('lev_pos');
export const DEVNET_RPC = 'https://api.devnet.solana.com';

interface PhantomProvider {
	publicKey: PublicKey;
	signTransaction: <T extends Transaction | VersionedTransaction>(tx: T) => Promise<T>;
	signAllTransactions: <T extends Transaction | VersionedTransaction>(txs: T[]) => Promise<T[]>;
}

export function getPhantom(): PhantomProvider {
	const phantom = (window as any).phantom?.solana;
	if (!phantom?.isPhantom) throw new Error('Phantom wallet not found');
	if (!phantom.publicKey) throw new Error('Phantom not connected');
	return phantom;
}

export function getProgram() {
	const phantom = getPhantom();
	const connection = new Connection(DEVNET_RPC, 'confirmed');
	const wallet = {
		publicKey: phantom.publicKey,
		signTransaction: phantom.signTransaction.bind(phantom),
		signAllTransactions: phantom.signAllTransactions.bind(phantom),
	};
	const provider = new AnchorProvider(connection, wallet as any, { commitment: 'confirmed' });
	return new Program(idl as Idl, provider);
}

export function leveragedPositionPda(authority: PublicKey, nonce: bigint): [PublicKey, number] {
	const nonceBytes = new Uint8Array(8);
	const view = new DataView(nonceBytes.buffer);
	view.setBigUint64(0, nonce, true); // little-endian
	return PublicKey.findProgramAddressSync(
		[LEVERAGED_SEED, authority.toBuffer(), nonceBytes],
		SENTINEL_PROGRAM_ID,
	);
}

export { BN };
