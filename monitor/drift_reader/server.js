const express = require('express');
const cors = require('cors');
const { Connection, Keypair, PublicKey } = require('@solana/web3.js');
const {
  DriftClient,
  Wallet,
  BulkAccountLoader,
  convertToNumber,
  QUOTE_PRECISION,
  BASE_PRECISION,
  PRICE_PRECISION,
  PerpMarkets,
  getUserAccountPublicKey,
} = require('@drift-labs/sdk');

const PORT = Number(process.env.PORT || 8002);
const RPC_URL = process.env.SOLANA_RPC_URL || 'https://api.devnet.solana.com';
const ENV = process.env.DRIFT_ENV || 'devnet';

const state = {
  client: null,
  ready: false,
  addedAuthorities: new Set(),
};

async function initClient() {
  if (state.client) return state.client;

  const conn = new Connection(RPC_URL, 'confirmed');
  const wallet = new Wallet(Keypair.generate());
  const loader = new BulkAccountLoader(conn, 'confirmed', 1000);

  const client = new DriftClient({
    connection: conn,
    wallet,
    env: ENV,
    accountSubscription: { type: 'polling', accountLoader: loader },
  });

  await client.subscribe();
  state.client = client;
  state.ready = true;
  console.log(`[drift] subscribed on ${ENV} (${RPC_URL})`);
  return client;
}

function perpMarketSymbol(marketIndex) {
  const entry = PerpMarkets[ENV]?.find((m) => m.marketIndex === marketIndex);
  return entry?.symbol || `PERP-${marketIndex}`;
}

function riskLevelFromHealth(health) {
  if (health >= 60) return 'Safe';
  if (health >= 30) return 'Warning';
  if (health >= 10) return 'Danger';
  return 'Critical';
}

async function loadUserPositions(walletAddress) {
  const client = await initClient();
  const authority = new PublicKey(walletAddress);

  const userPubkey = await getUserAccountPublicKey(
    client.program.programId,
    authority,
    0,
  );

  const info = await client.connection.getAccountInfo(userPubkey);
  if (!info) {
    return {
      hasAccount: false,
      positions: [],
      summary: null,
    };
  }

  if (!state.addedAuthorities.has(walletAddress)) {
    await client.addUser(0, authority);
    state.addedAuthorities.add(walletAddress);
  }

  const user = client.getUser(0, authority);
  await user.fetchAccounts();

  const activePerps = user.getActivePerpPositions();
  const totalCollateral = convertToNumber(user.getTotalCollateral(), QUOTE_PRECISION);
  const freeCollateral = convertToNumber(user.getFreeCollateral(), QUOTE_PRECISION);
  const leverage = convertToNumber(user.getLeverage(), new (require('bn.js'))(10_000));
  const health = user.getHealth();

  const positions = activePerps.map((p, idx) => {
    const marketIndex = p.marketIndex;
    const perpMarket = client.getPerpMarketAccount(marketIndex);
    const oraclePrice = client.getOracleDataForPerpMarket(marketIndex).price;
    const baseAmount = convertToNumber(p.baseAssetAmount, BASE_PRECISION);
    const quoteAmount = convertToNumber(p.quoteAssetAmount, QUOTE_PRECISION);
    const oracle = convertToNumber(oraclePrice, PRICE_PRECISION);

    const direction = baseAmount > 0 ? 'LONG' : baseAmount < 0 ? 'SHORT' : 'FLAT';
    const notional = Math.abs(baseAmount * oracle);
    const entryPrice = baseAmount !== 0 ? Math.abs(quoteAmount / baseAmount) : 0;
    // PnL for any direction: mark-to-market value + accumulated quote-asset flow.
    // For longs baseAmount>0 (we own base, we owe quote = negative quoteAmount).
    // For shorts baseAmount<0 (we owe base, we hold quote = positive quoteAmount).
    const unrealizedPnl = baseAmount * oracle + quoteAmount;

    return {
      id: `drift-${marketIndex}-${idx}`,
      protocol: 'Drift',
      asset: perpMarketSymbol(marketIndex),
      direction,
      baseSize: Math.abs(baseAmount),
      notional: Number(notional.toFixed(2)),
      entryPrice: Number(entryPrice.toFixed(4)),
      oraclePrice: Number(oracle.toFixed(4)),
      unrealizedPnl: Number(unrealizedPnl.toFixed(2)),
      collateral: Number(totalCollateral.toFixed(2)),
      debt: Number(Math.max(notional - totalCollateral, 0).toFixed(2)),
      healthFactor: Number((health / 100 * 5).toFixed(2)),
      healthPercent: health,
      leverage: Number(leverage.toFixed(2)),
      riskLevel: riskLevelFromHealth(health),
      lastChecked: 'just now',
      source: 'drift-devnet',
    };
  });

  return {
    hasAccount: true,
    positions,
    summary: {
      totalCollateral: Number(totalCollateral.toFixed(2)),
      freeCollateral: Number(freeCollateral.toFixed(2)),
      leverage: Number(leverage.toFixed(2)),
      health,
    },
  };
}

const app = express();
app.use(cors());

app.get('/health', (_req, res) => {
  res.json({ ok: true, ready: state.ready, env: ENV, rpc: RPC_URL });
});

app.get('/positions/:wallet', async (req, res) => {
  const { wallet } = req.params;
  try {
    new PublicKey(wallet);
  } catch {
    return res.status(400).json({ error: 'invalid wallet address' });
  }

  try {
    const data = await loadUserPositions(wallet);
    res.json(data);
  } catch (err) {
    console.error('[drift] positions error', err?.message);
    res.status(500).json({ error: err?.message || 'read failed' });
  }
});

app.listen(PORT, () => {
  console.log(`[drift] reader listening on :${PORT}`);
  initClient().catch((e) => {
    console.error('[drift] init failed:', e?.message);
  });
});
