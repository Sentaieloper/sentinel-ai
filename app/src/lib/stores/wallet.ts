import { writable } from 'svelte/store';

interface WalletState {
	connected: boolean;
	address: string | null;
}

export const walletStore = writable<WalletState>({
	connected: false,
	address: null,
});

export async function connectPhantom(): Promise<boolean> {
	if (typeof window === 'undefined') return false;

	const phantom = (window as any).phantom?.solana;
	if (!phantom?.isPhantom) {
		window.open('https://phantom.app/', '_blank');
		return false;
	}

	try {
		const response = await phantom.connect();
		const pubkey = response.publicKey.toString();
		walletStore.set({ connected: true, address: pubkey });
		return true;
	} catch {
		return false;
	}
}

export async function disconnectPhantom(): Promise<void> {
	if (typeof window === 'undefined') return;

	const phantom = (window as any).phantom?.solana;
	if (phantom) {
		try {
			await phantom.disconnect();
		} catch {
			// silent
		}
	}
	walletStore.set({ connected: false, address: null });
}

export function abbreviateAddress(addr: string): string {
	if (addr.length <= 10) return addr;
	return `${addr.slice(0, 4)}...${addr.slice(-4)}`;
}
