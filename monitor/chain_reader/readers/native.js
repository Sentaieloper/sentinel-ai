const { LAMPORTS_PER_SOL } = require('@solana/web3.js');

async function read(connection, wallet) {
	const lamports = await connection.getBalance(wallet, 'confirmed');
	if (lamports === 0) return [];
	const sol = lamports / LAMPORTS_PER_SOL;
	return [
		{
			id: `native-${wallet.toBase58()}`,
			protocol: 'Native',
			asset: 'SOL',
			balance: sol,
			lamports,
			riskLevel: 'Safe',
			source: 'native',
			lastChecked: 'just now',
		},
	];
}

module.exports = { read };
