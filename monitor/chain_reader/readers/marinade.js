const { PublicKey } = require('@solana/web3.js');
const { getAssociatedTokenAddressSync, getAccount, TokenAccountNotFoundError } = require('@solana/spl-token');

// mSOL mint is identical across clusters per Marinade docs. Marinade-mainnet
// is the only deployment with a live state account; on devnet there is no
// Marinade stake pool, so mSOL ATAs almost never exist. If they do, we only
// report the raw balance (no fake sol-equivalent).
const MSOL_MINT = new PublicKey('mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So');

async function read(connection, wallet) {
	const ata = getAssociatedTokenAddressSync(MSOL_MINT, wallet, true);
	let balance = 0;
	try {
		const acc = await getAccount(connection, ata);
		balance = Number(acc.amount) / 1e9;
	} catch (e) {
		if (e instanceof TokenAccountNotFoundError) return [];
		if (/TokenAccountNotFound/i.test(String(e?.name || e))) return [];
		throw e;
	}
	if (balance <= 0) return [];

	return [
		{
			id: `marinade-msol-${wallet.toBase58()}`,
			protocol: 'Marinade',
			asset: 'mSOL',
			balance,
			// exchangeRate and solEquivalent intentionally omitted on devnet —
			// we do not have a reliable Marinade state account here. UI will
			// fall back to showing balance only.
			riskLevel: 'Safe',
			source: 'marinade',
			lastChecked: 'just now',
		},
	];
}

module.exports = { read };
