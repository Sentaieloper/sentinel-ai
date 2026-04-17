const express = require('express');
const cors = require('cors');
const { Connection, PublicKey, LAMPORTS_PER_SOL } = require('@solana/web3.js');
const { getAccount, getAssociatedTokenAddressSync, TOKEN_PROGRAM_ID } = require('@solana/spl-token');

const marinadeReader = require('./readers/marinade');
const splReader = require('./readers/spl');
const nativeReader = require('./readers/native');
const kaminoReader = require('./readers/kamino');
const marginfiReader = require('./readers/marginfi');

const PORT = Number(process.env.PORT || 8003);
const RPC_URL = process.env.SOLANA_RPC_URL || 'https://api.devnet.solana.com';

const connection = new Connection(RPC_URL, 'confirmed');

function safeWallet(raw) {
	try {
		return new PublicKey(raw);
	} catch {
		return null;
	}
}

function wrapReader(name, handler) {
	return async (req, res) => {
		const wallet = safeWallet(req.params.wallet);
		if (!wallet) return res.status(400).json({ error: 'invalid wallet' });
		try {
			const positions = await handler(connection, wallet);
			res.json({ protocol: name, positions });
		} catch (e) {
			console.warn(`[${name}] read failed:`, e?.message);
			res.status(200).json({ protocol: name, positions: [], error: e?.message || 'read failed' });
		}
	};
}

const app = express();
app.use(cors());

app.get('/health', (_req, res) => {
	res.json({ ok: true, rpc: RPC_URL, port: PORT });
});

app.get('/native/:wallet', wrapReader('native', nativeReader.read));
app.get('/spl/:wallet', wrapReader('spl', splReader.read));
app.get('/marinade/:wallet', wrapReader('marinade', marinadeReader.read));
app.get('/kamino/:wallet', wrapReader('kamino', kaminoReader.read));
app.get('/marginfi/:wallet', wrapReader('marginfi', marginfiReader.read));

app.get('/all/:wallet', async (req, res) => {
	const wallet = safeWallet(req.params.wallet);
	if (!wallet) return res.status(400).json({ error: 'invalid wallet' });

	const tasks = [
		['native', nativeReader.read],
		['spl', splReader.read],
		['marinade', marinadeReader.read],
		['kamino', kaminoReader.read],
		['marginfi', marginfiReader.read],
	];

	const results = await Promise.all(
		tasks.map(async ([name, handler]) => {
			try {
				const positions = await handler(connection, wallet);
				return { protocol: name, positions };
			} catch (e) {
				return { protocol: name, positions: [], error: e?.message || 'read failed' };
			}
		}),
	);

	res.json({ wallet: wallet.toBase58(), results });
});

app.listen(PORT, () => {
	console.log(`[chain_reader] listening on :${PORT} (rpc=${RPC_URL})`);
});
