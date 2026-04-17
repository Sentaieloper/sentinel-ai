const { PublicKey, Keypair } = require('@solana/web3.js');

let mfi = null;
function loadSdk() {
	if (!mfi) {
		try {
			mfi = require('@mrgnlabs/marginfi-client-v2');
		} catch (e) {
			mfi = { error: e.message };
		}
	}
	return mfi;
}

function riskFromHealth(h) {
	if (h == null) return 'Safe';
	if (h >= 0.8) return 'Safe';
	if (h >= 0.5) return 'Warning';
	if (h >= 0.2) return 'Danger';
	return 'Critical';
}

async function read(connection, wallet) {
	const sdk = loadSdk();
	if (!sdk?.MarginfiClient || !sdk?.getConfig) {
		throw new Error(sdk?.error || 'marginfi-client-v2 missing exports');
	}
	const { MarginfiClient, getConfig } = sdk;

	const config = getConfig('dev');
	// Read-only wallet wrapper — no signing done in this service
	const readOnlyWallet = {
		publicKey: wallet,
		signTransaction: async (tx) => tx,
		signAllTransactions: async (txs) => txs,
	};

	const client = await MarginfiClient.fetch(config, readOnlyWallet, connection, { readOnly: true });
	let addresses = [];
	try {
		addresses = await client.getMarginfiAccountAddressesByAuthority?.(wallet) || [];
	} catch {
		addresses = [];
	}
	if (!addresses?.length && typeof client.getMarginfiAccountsForAuthority === 'function') {
		try {
			const accs = await client.getMarginfiAccountsForAuthority(wallet);
			addresses = accs.map((a) => a.address);
		} catch {
			addresses = [];
		}
	}
	if (!addresses?.length) return [];

	const out = [];
	for (const addr of addresses) {
		try {
			const account = await client.getMarginfiAccount(addr);
			if (!account) continue;
			const summary = account.computeHealthComponents
				? account.computeHealthComponents(2) // MaintenanceRequirement
				: null;
			const assets = Number(summary?.assets || 0);
			const liabs = Number(summary?.liabilities || 0);
			const health = assets > 0 ? (assets - liabs) / assets : 1;

			const balances = account.balances || [];
			const depositAssets = [];
			const borrowAssets = [];
			for (const b of balances) {
				try {
					const bank = client.getBankByPk?.(b.bankPk);
					const symbol = bank?.tokenSymbol || bank?.mint?.toBase58?.().slice(0, 4) || 'asset';
					if (b.computeQuantityUi && bank) {
						const { assets: a, liabilities: l } = b.computeQuantityUi(bank);
						if (Number(a) > 0.0001) depositAssets.push(symbol);
						if (Number(l) > 0.0001) borrowAssets.push(symbol);
					}
				} catch { /* skip */ }
			}
			const label = borrowAssets.length
				? `${depositAssets.join('/') || 'mixed'} → ${borrowAssets.join('/')}`
				: depositAssets.join('/') || 'supply only';

			out.push({
				id: `marginfi-${addr.toBase58?.() || String(addr)}`,
				protocol: 'MarginFi',
				asset: label,
				collateral: Number(assets.toFixed(2)),
				debt: Number(liabs.toFixed(2)),
				healthFactor: Number(((health + 1) * 2).toFixed(2)), // scale 0..1 -> 2..4
				healthPercent: Number((Math.max(health, 0) * 100).toFixed(1)),
				riskLevel: riskFromHealth(health),
				source: 'marginfi',
				lastChecked: 'just now',
			});
		} catch (e) {
			// skip broken account
		}
	}
	return out;
}

module.exports = { read };
