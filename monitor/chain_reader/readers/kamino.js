const { PublicKey } = require('@solana/web3.js');

let klend = null;
function loadSdk() {
	if (!klend) {
		try {
			klend = require('@kamino-finance/klend-sdk');
		} catch (e) {
			klend = { error: e.message };
		}
	}
	return klend;
}

// Kamino lending program id (same on mainnet + devnet per docs)
const PROGRAM_ID = new PublicKey('KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD');
// Main market on devnet — same deployment ID as mainnet main market
const MAIN_MARKET = new PublicKey('7u3HeHxYDLhnCoErrtycNokbQYbWGzLs9JsrifqDqCYD');

const SLOT_DURATION_MS = 450;

function riskFromLtv(ltv, liquidationLtv) {
	if (!liquidationLtv || liquidationLtv <= 0) return 'Safe';
	const utilization = ltv / liquidationLtv;
	if (utilization >= 0.95) return 'Critical';
	if (utilization >= 0.85) return 'Danger';
	if (utilization >= 0.70) return 'Warning';
	return 'Safe';
}

async function read(connection, wallet) {
	const sdk = loadSdk();
	if (!sdk?.KaminoMarket) {
		throw new Error(sdk?.error || 'klend-sdk missing KaminoMarket export');
	}
	const { KaminoMarket } = sdk;

	const market = await KaminoMarket.load(connection, MAIN_MARKET, SLOT_DURATION_MS, PROGRAM_ID);
	if (!market) return [];

	let obligations = [];
	try {
		if (typeof market.getAllUserObligations === 'function') {
			obligations = await market.getAllUserObligations(wallet);
		} else if (typeof market.getObligationByAddress === 'function') {
			// fallback
			obligations = [];
		}
	} catch (e) {
		throw new Error(`obligation fetch failed: ${e.message}`);
	}

	const out = [];
	for (const obligation of obligations || []) {
		try {
			const stats = obligation.refreshedStats || obligation.getStats?.() || {};
			const deposits = obligation.deposits ? Array.from(obligation.deposits.values()) : [];
			const borrows = obligation.borrows ? Array.from(obligation.borrows.values()) : [];

			const depositUsd = Number(stats.userTotalDeposit || 0);
			const borrowUsd = Number(stats.userTotalBorrow || 0);
			const ltv = Number(stats.loanToValue || 0);
			const liquidationLtv = Number(stats.liquidationLtv || 0);
			const hf = liquidationLtv > 0 ? liquidationLtv / Math.max(ltv, 0.0001) : 0;

			const depositAssets = deposits.map((d) => d.reserve?.symbol || d.symbol || 'asset').join('/');
			const borrowAssets = borrows.map((b) => b.reserve?.symbol || b.symbol || 'asset').join('/');
			const label = borrowUsd > 0
				? `${depositAssets || 'mixed'} → ${borrowAssets || 'loan'}`
				: `${depositAssets || 'supply only'}`;

			out.push({
				id: `kamino-${obligation.obligationAddress?.toBase58?.() || obligation.pubkey?.toBase58?.() || Math.random()}`,
				protocol: 'Kamino',
				asset: label,
				collateral: Number(depositUsd.toFixed(2)),
				debt: Number(borrowUsd.toFixed(2)),
				healthFactor: Number((isFinite(hf) ? hf : 0).toFixed(2)),
				ltv: Number(ltv.toFixed(4)),
				liquidationLtv: Number(liquidationLtv.toFixed(4)),
				riskLevel: riskFromLtv(ltv, liquidationLtv),
				source: 'kamino',
				lastChecked: 'just now',
			});
		} catch (e) {
			// skip broken obligation
		}
	}
	return out;
}

module.exports = { read };
