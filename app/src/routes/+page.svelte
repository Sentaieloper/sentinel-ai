<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { walletStore } from '$lib/stores/wallet';

	type Blip = {
		id: number;
		angle: number;
		radius: number;
		label: string;
		severity: 'safe' | 'warning' | 'critical';
		acquired: boolean;
	};

	const PROTOCOLS = [
		{ label: 'KAMINO',   severity: 'safe' as const },
		{ label: 'MARGINFI', severity: 'safe' as const },
		{ label: 'MARINADE', severity: 'safe' as const },
		{ label: 'PYTH',     severity: 'safe' as const },
		{ label: 'SOL-PERP', severity: 'warning' as const },
		{ label: 'BTC-PERP', severity: 'safe' as const },
		{ label: 'ETH-PERP', severity: 'warning' as const },
		{ label: 'JITOSOL',  severity: 'safe' as const },
		{ label: 'USDC',     severity: 'safe' as const },
		{ label: 'mSOL',     severity: 'safe' as const },
		{ label: 'HF:1.08',  severity: 'critical' as const },
		{ label: 'HF:1.35',  severity: 'warning' as const },
	];

	let blips: Blip[] = [];
	let sweepAngle = 0;
	let tickCount = 0;
	let opsTime = '';
	let threatLevel: 'NOMINAL' | 'ELEVATED' | 'HIGH' = 'NOMINAL';
	let uptime = '00:00:00';
	let blipCounter = 0;
	let bootLines: string[] = [];
	let blinkCaret = true;

	let sweepTimer: any;
	let blipTimer: any;
	let clockTimer: any;
	let caretTimer: any;
	const bootTimers: any[] = [];
	const mountedAt = Date.now();

	// Seed synchronously so SSR render shows the radar with blips instead
	// of flashing empty then populating in onMount.
	for (let i = 0; i < 7; i++) blips.push(randomBlip());

	const BOOT_SEQUENCE = [
		'[OK] boot.init             ',
		'[OK] solana.devnet.rpc     ',
		'[OK] pyth.hermes.feeds     ',
		'[OK] kamino.klend.sdk      ',
		'[OK] marginfi.client.v2    ',
		'[OK] marinade.token.read   ',
		'[OK] sentinel.anchor.idl   ',
		'[OK] xgboost.predictor     ',
		'[**] sentinel online.      ',
	];

	function randomBlip(): Blip {
		const p = PROTOCOLS[Math.floor(Math.random() * PROTOCOLS.length)];
		return {
			id: blipCounter++,
			angle: Math.random() * 360,
			radius: 40 + Math.random() * 150,
			label: p.label,
			severity: p.severity,
			acquired: false,
		};
	}

	function pad(n: number) { return String(n).padStart(2, '0'); }

	function updateClock() {
		const d = new Date();
		opsTime = `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`;
		const s = Math.floor((Date.now() - mountedAt) / 1000);
		uptime = `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`;
	}

	function initiateKeyListener(e: KeyboardEvent) {
		if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
			e.preventDefault();
			initiate();
		}
	}

	onMount(() => {
		// boot sequence
		BOOT_SEQUENCE.forEach((line, i) => {
			const t = setTimeout(() => {
				bootLines = [...bootLines, line];
			}, 140 * i);
			bootTimers.push(t);
		});

		// radar sweep
		sweepTimer = setInterval(() => {
			sweepAngle = (sweepAngle + 2) % 360;
			tickCount += 1;
			// acquire blips under the beam
			blips = blips.map((b) => {
				const delta = Math.abs(((b.angle - sweepAngle + 540) % 360) - 180);
				if (delta > 172 && !b.acquired) {
					return { ...b, acquired: true };
				}
				return b;
			});
		}, 30);

		// spawn/retire blips
		blipTimer = setInterval(() => {
			if (blips.length > 10) blips = blips.slice(1);
			blips = [...blips, randomBlip()];
			// rotate threat level
			const critical = blips.filter((b) => b.severity === 'critical' && b.acquired).length;
			const warning  = blips.filter((b) => b.severity === 'warning'  && b.acquired).length;
			if (critical > 0) threatLevel = 'HIGH';
			else if (warning >= 2) threatLevel = 'ELEVATED';
			else threatLevel = 'NOMINAL';
		}, 2500);

		clockTimer = setInterval(updateClock, 1000);
		caretTimer = setInterval(() => (blinkCaret = !blinkCaret), 600);
		updateClock();
	});

	onDestroy(() => {
		clearInterval(sweepTimer);
		clearInterval(blipTimer);
		clearInterval(clockTimer);
		clearInterval(caretTimer);
		bootTimers.forEach(clearTimeout);
	});

	function initiate() {
		goto('/dashboard');
	}

	$: walletLabel = $walletStore.connected && $walletStore.address
		? `${$walletStore.address.slice(0, 4)}…${$walletStore.address.slice(-4)}`
		: 'NO OPERATOR';

	$: threatColor = threatLevel === 'HIGH'
		? 'var(--critical)'
		: threatLevel === 'ELEVATED'
		? 'var(--warning)'
		: 'var(--safe)';
</script>

<svelte:head>
	<title>Sentinel AI — Tactical Console</title>
</svelte:head>

<svelte:window on:keydown={initiateKeyListener} />

<div class="tac-root">
	<!-- Left HUD: boot log -->
	<div class="hud hud-left">
		<div class="hud-label">
			<span class="hud-dot"></span>
			SYS.BOOT
		</div>
		<div class="boot-log">
			{#each bootLines as line, i}
				<div class="boot-line" style="animation-delay: {i * 60}ms">{line}</div>
			{/each}
			<div class="boot-line caret">> awaiting operator{blinkCaret ? '_' : ' '}</div>
		</div>

		<div class="hud-label" style="margin-top: 14px;">
			<span class="hud-dot"></span>
			OPERATOR
		</div>
		<div class="hud-kv">
			<span class="k">ID</span>
			<span class="v {$walletStore.connected ? 'v-ok' : 'v-dim'}">{walletLabel}</span>
		</div>
		<div class="hud-kv">
			<span class="k">CLUSTER</span>
			<span class="v v-ok">solana.devnet</span>
		</div>
		<div class="hud-kv">
			<span class="k">LINK</span>
			<span class="v v-ok">HELIUS/PYTH</span>
		</div>
	</div>

	<!-- Center Radar -->
	<div class="radar-wrap">
		<div class="radar-title">SENTINEL SCAN — DEVNET AREA</div>
		<div class="radar">
			<!-- range rings -->
			<div class="ring r1"></div>
			<div class="ring r2"></div>
			<div class="ring r3"></div>
			<div class="ring r4"></div>
			<!-- cross axes -->
			<div class="axis axis-h"></div>
			<div class="axis axis-v"></div>
			<!-- sweep -->
			<div class="sweep" style="transform: rotate({sweepAngle}deg)"></div>
			<!-- center pulse -->
			<div class="center-pulse"></div>

			<!-- blips -->
			{#each blips as b (b.id)}
				{@const rad = (b.angle * Math.PI) / 180}
				{@const cx = 50 + Math.cos(rad) * (b.radius / 4)}
				{@const cy = 50 + Math.sin(rad) * (b.radius / 4)}
				<div
					class="blip blip-{b.severity}"
					class:acquired={b.acquired}
					style="left: {cx}%; top: {cy}%;"
				>
					<span class="blip-dot"></span>
					{#if b.acquired}
						<span class="blip-label">{b.label}</span>
					{/if}
				</div>
			{/each}
		</div>
		<div class="radar-foot">
			<span>RANGE 2500km</span>
			<span>BEAM {sweepAngle.toString().padStart(3, '0')}°</span>
			<span>TICK {tickCount.toLocaleString()}</span>
		</div>

		<div class="briefing">
			<div class="briefing-head">
				<span class="brief-label">▸ MISSION BRIEFING</span>
				<span class="brief-code">CLASS-01 · OPEN</span>
			</div>
			<div class="briefing-body">
				<p>
					<strong>Sentinel AI</strong> is a tactical console that watches your DeFi positions on
					<strong>Solana devnet</strong> in real time and warns before things get liquidated.
				</p>
				<div class="brief-grid">
					<div>
						<div class="brief-k">TARGETS</div>
						<div class="brief-v">Kamino · MarginFi · Marinade · Sentinel Perps · wallet balances</div>
					</div>
					<div>
						<div class="brief-k">SIGNALS</div>
						<div class="brief-v">Pyth Hermes oracles · on-chain Anchor program · devnet SDKs</div>
					</div>
					<div>
						<div class="brief-k">OUTPUT</div>
						<div class="brief-v">Live health factor · liquidation price · bot-generated advice</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Right HUD: systems + threat -->
	<div class="hud hud-right">
		<div class="hud-label">
			<span class="hud-dot dot-red"></span>
			THREAT LEVEL
		</div>
		<div class="threat" style="color: {threatColor}; border-color: {threatColor}">
			<div class="threat-value">{threatLevel}</div>
			<div class="threat-meter">
				<div class="threat-fill" style="
					background: {threatColor};
					width: {threatLevel === 'HIGH' ? 100 : threatLevel === 'ELEVATED' ? 60 : 25}%
				"></div>
			</div>
		</div>

		<div class="hud-label" style="margin-top: 16px;">
			<span class="hud-dot"></span>
			TRACKED PROTOCOLS
		</div>
		<div class="proto-list">
			{#each ['Sentinel Perps', 'Kamino', 'MarginFi', 'Marinade', 'Wallet', 'Pyth oracles'] as p}
				<div class="proto-row">
					<span class="proto-mark"></span>
					<span class="proto-name">{p}</span>
					<span class="proto-ok">LIVE</span>
				</div>
			{/each}
		</div>

		<div class="hud-label" style="margin-top: 16px;">
			<span class="hud-dot"></span>
			METRICS
		</div>
		<div class="hud-kv">
			<span class="k">OPS.TIME</span>
			<span class="v v-mono">{opsTime}</span>
		</div>
		<div class="hud-kv">
			<span class="k">UPTIME</span>
			<span class="v v-mono">{uptime}</span>
		</div>
		<div class="hud-kv">
			<span class="k">BLIPS</span>
			<span class="v v-mono">{blips.length}</span>
		</div>
	</div>

	<!-- CTA -->
	<div class="cta-wrap">
		<button class="cta" on:click={initiate}>
			<span class="cta-bracket">&gt;</span>
			INITIATE MONITORING
			<span class="cta-bracket">&lt;</span>
		</button>
		<div class="cta-sub">Enter the tactical console · Ctrl+K to jump</div>
	</div>

	<!-- Corners -->
	<div class="corner tl"></div>
	<div class="corner tr"></div>
	<div class="corner bl"></div>
	<div class="corner br"></div>

	<!-- Scanlines + noise -->
	<div class="scanlines"></div>
	<div class="vignette"></div>
</div>

<style>
	:global(body) {
		overflow: hidden;
	}

	.tac-root {
		position: fixed;
		inset: 0;
		top: 60px; /* topbar height */
		display: grid;
		grid-template-columns: 280px 1fr 280px;
		grid-template-rows: 1fr auto;
		gap: 18px;
		padding: 18px;
		background:
			radial-gradient(ellipse at center, rgba(61, 220, 132, 0.04) 0%, transparent 60%),
			linear-gradient(180deg, #070d07 0%, #0a0f0a 100%);
		overflow: hidden;
	}

	/* corners */
	.corner {
		position: absolute;
		width: 28px;
		height: 28px;
		border: 1px solid var(--accent-green);
		opacity: 0.6;
	}
	.tl { top: 10px; left: 10px; border-right: none; border-bottom: none; }
	.tr { top: 10px; right: 10px; border-left: none; border-bottom: none; }
	.bl { bottom: 10px; left: 10px; border-right: none; border-top: none; }
	.br { bottom: 10px; right: 10px; border-left: none; border-top: none; }

	.scanlines {
		position: absolute;
		inset: 0;
		background: repeating-linear-gradient(
			0deg,
			rgba(61, 220, 132, 0.03) 0px,
			rgba(61, 220, 132, 0.03) 1px,
			transparent 1px,
			transparent 3px
		);
		pointer-events: none;
		mix-blend-mode: screen;
		animation: scan-shift 8s linear infinite;
	}

	.vignette {
		position: absolute;
		inset: 0;
		background: radial-gradient(
			ellipse at center,
			transparent 40%,
			rgba(0, 0, 0, 0.55) 100%
		);
		pointer-events: none;
	}

	@keyframes scan-shift {
		from { background-position: 0 0; }
		to { background-position: 0 3px; }
	}

	/* HUD panels */
	.hud {
		background: rgba(10, 15, 10, 0.65);
		border: 1px solid var(--border-bright);
		border-radius: 3px;
		padding: 16px;
		backdrop-filter: blur(6px);
		font-family: 'IBM Plex Mono', monospace;
		animation: hud-enter 480ms cubic-bezier(0.2, 0.9, 0.3, 1) both;
	}
	.hud-left  { animation-delay: 0ms;  }
	.hud-right { animation-delay: 120ms; }

	@keyframes hud-enter {
		from { opacity: 0; transform: translateX(-10px); filter: blur(6px); }
		to   { opacity: 1; transform: none; filter: blur(0); }
	}
	.hud-right { animation-name: hud-enter-right; }
	@keyframes hud-enter-right {
		from { opacity: 0; transform: translateX(10px); filter: blur(6px); }
		to   { opacity: 1; transform: none; filter: blur(0); }
	}

	.hud-label {
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 2px;
		color: var(--text-dim);
		margin-bottom: 8px;
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.hud-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--accent-green);
		box-shadow: 0 0 6px var(--accent-green);
		animation: pulse-hud 1.6s ease-in-out infinite;
	}
	.hud-dot.dot-red {
		background: var(--critical);
		box-shadow: 0 0 6px var(--critical);
	}

	@keyframes pulse-hud {
		0%, 100% { opacity: 1; }
		50%      { opacity: 0.3; }
	}

	.boot-log {
		font-size: 10px;
		line-height: 1.55;
		color: var(--text-secondary);
		max-height: 170px;
		overflow: hidden;
	}

	.boot-line {
		white-space: pre;
		animation: boot-in 220ms steps(40, end) both;
		color: var(--safe);
	}
	.boot-line.caret { color: var(--text-dim); margin-top: 4px; }

	@keyframes boot-in {
		from { clip-path: inset(0 100% 0 0); opacity: 0.4; }
		to   { clip-path: inset(0 0 0 0);    opacity: 1; }
	}

	.hud-kv {
		display: flex;
		justify-content: space-between;
		font-size: 10px;
		line-height: 1.8;
	}
	.hud-kv .k { color: var(--text-dim); letter-spacing: 1px; }
	.hud-kv .v { color: var(--text-primary); font-weight: 500; }
	.hud-kv .v-ok { color: var(--safe); }
	.hud-kv .v-dim { color: var(--text-dim); }
	.hud-kv .v-mono { font-variant-numeric: tabular-nums; }

	/* threat */
	.threat {
		border: 1px solid;
		border-radius: 3px;
		padding: 10px;
		margin-bottom: 4px;
	}
	.threat-value {
		font-size: 18px;
		font-weight: 800;
		letter-spacing: 3px;
		text-align: center;
		margin-bottom: 6px;
		animation: threat-flash 2s ease-in-out infinite;
	}
	@keyframes threat-flash {
		0%, 100% { text-shadow: 0 0 4px currentColor; }
		50%      { text-shadow: 0 0 14px currentColor; }
	}
	.threat-meter {
		height: 4px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 2px;
		overflow: hidden;
	}
	.threat-fill {
		height: 100%;
		transition: width 400ms ease, background 400ms ease;
	}

	.proto-list {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.proto-row {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 10px;
		padding: 3px 0;
	}
	.proto-mark {
		width: 4px;
		height: 4px;
		background: var(--accent-green);
		border-radius: 50%;
	}
	.proto-name {
		flex: 1;
		color: var(--text-secondary);
	}
	.proto-ok {
		font-size: 8px;
		font-weight: 700;
		color: var(--safe);
		letter-spacing: 1px;
	}

	/* Radar */
	.radar-wrap {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 10px;
		animation: radar-enter 700ms cubic-bezier(0.2, 0.9, 0.3, 1) both;
	}
	@keyframes radar-enter {
		from { opacity: 0; transform: scale(0.94); filter: blur(8px); }
		to   { opacity: 1; transform: none;        filter: blur(0); }
	}

	.radar-title {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 3px;
		color: var(--text-dim);
	}
	.radar {
		position: relative;
		width: min(65vh, 520px);
		aspect-ratio: 1 / 1;
		border-radius: 50%;
		background:
			radial-gradient(circle at center, rgba(61, 220, 132, 0.06) 0%, transparent 60%),
			rgba(10, 20, 10, 0.7);
		border: 1px solid rgba(61, 220, 132, 0.35);
		box-shadow:
			inset 0 0 80px rgba(61, 220, 132, 0.08),
			0 0 40px rgba(61, 220, 132, 0.1);
		overflow: hidden;
	}

	.ring {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		border: 1px solid rgba(61, 220, 132, 0.18);
		border-radius: 50%;
	}
	.r1 { width: 25%; height: 25%; }
	.r2 { width: 50%; height: 50%; }
	.r3 { width: 75%; height: 75%; }
	.r4 { width: 100%; height: 100%; border-color: rgba(61, 220, 132, 0.28); }

	.axis {
		position: absolute;
		background: rgba(61, 220, 132, 0.12);
	}
	.axis-h { top: 50%; left: 0; right: 0; height: 1px; }
	.axis-v { left: 50%; top: 0; bottom: 0; width: 1px; }

	.sweep {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border-radius: 50%;
		transform-origin: center;
		background: conic-gradient(
			from -90deg,
			transparent 0deg,
			transparent 300deg,
			rgba(61, 220, 132, 0.02) 315deg,
			rgba(61, 220, 132, 0.08) 330deg,
			rgba(61, 220, 132, 0.18) 342deg,
			rgba(61, 220, 132, 0.35) 354deg,
			rgba(61, 220, 132, 0.55) 360deg
		);
		pointer-events: none;
		mask: radial-gradient(circle at center, transparent 0%, #000 6%, #000 100%);
		-webkit-mask: radial-gradient(circle at center, transparent 0%, #000 6%, #000 100%);
	}


	.center-pulse {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 10px;
		height: 10px;
		margin: -5px 0 0 -5px;
		border-radius: 50%;
		background: var(--accent-green);
		box-shadow: 0 0 8px var(--accent-green);
		animation: center-pulse 1.4s ease-in-out infinite;
	}
	@keyframes center-pulse {
		0%, 100% { transform: scale(1);  box-shadow: 0 0 8px var(--accent-green); }
		50%      { transform: scale(1.6); box-shadow: 0 0 18px var(--accent-green); }
	}

	.blip {
		position: absolute;
		transform: translate(-50%, -50%);
		pointer-events: none;
	}
	.blip-dot {
		display: block;
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: currentColor;
		box-shadow: 0 0 10px currentColor;
	}
	.blip-label {
		position: absolute;
		left: 10px;
		top: -5px;
		font-size: 8px;
		font-weight: 700;
		letter-spacing: 1px;
		color: currentColor;
		white-space: nowrap;
		text-shadow: 0 0 6px currentColor;
		animation: label-in 300ms ease both;
	}
	@keyframes label-in {
		from { opacity: 0; transform: translateX(-3px); }
		to   { opacity: 1; transform: none; }
	}
	.blip.acquired .blip-dot {
		animation: blip-flash 2.2s ease-out forwards;
	}
	@keyframes blip-flash {
		0%   { transform: scale(2.2); opacity: 1; }
		20%  { transform: scale(1);   opacity: 1; }
		100% { transform: scale(1);   opacity: 0.35; }
	}

	.blip-safe     { color: var(--safe); }
	.blip-warning  { color: var(--warning); }
	.blip-critical { color: var(--critical); }

	.radar-foot {
		display: flex;
		gap: 22px;
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 2px;
		color: var(--text-dim);
		font-variant-numeric: tabular-nums;
	}

	.briefing {
		width: min(720px, 92%);
		margin-top: 14px;
		border: 1px solid var(--border-bright);
		background: rgba(10, 20, 10, 0.55);
		padding: 12px 16px;
		font-family: 'IBM Plex Mono', monospace;
		animation: hud-enter 520ms cubic-bezier(0.2, 0.9, 0.3, 1) both;
		animation-delay: 260ms;
	}

	.briefing-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-bottom: 1px dashed rgba(61, 220, 132, 0.25);
		padding-bottom: 6px;
		margin-bottom: 8px;
	}

	.brief-label {
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 2px;
		color: var(--accent-green);
	}

	.brief-code {
		font-size: 8px;
		color: var(--text-dim);
		letter-spacing: 1.5px;
	}

	.briefing-body p {
		font-size: 11px;
		line-height: 1.55;
		color: var(--text-secondary);
		margin-bottom: 10px;
	}

	.briefing-body p strong {
		color: var(--accent-green);
		font-weight: 700;
	}

	.brief-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 14px;
	}

	.brief-k {
		font-size: 8px;
		font-weight: 700;
		letter-spacing: 2px;
		color: var(--text-dim);
		margin-bottom: 3px;
	}

	.brief-v {
		font-size: 10px;
		color: var(--text-primary);
		line-height: 1.45;
	}

	@media (max-width: 900px) {
		.brief-grid { grid-template-columns: 1fr; }
	}

	/* CTA */
	.cta-wrap {
		grid-column: 1 / -1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		padding-bottom: 8px;
	}

	.cta {
		background: transparent;
		border: 1px solid var(--accent-green);
		color: var(--accent-green);
		font-family: 'IBM Plex Mono', monospace;
		font-size: 13px;
		font-weight: 800;
		letter-spacing: 4px;
		padding: 12px 28px;
		cursor: pointer;
		position: relative;
		overflow: hidden;
		transition: all 200ms ease;
		animation: cta-breath 3s ease-in-out infinite;
	}

	.cta:hover {
		background: var(--accent-green);
		color: #000;
		letter-spacing: 5px;
	}

	.cta-bracket {
		display: inline-block;
		margin: 0 8px;
		opacity: 0.5;
	}

	.cta:hover .cta-bracket { opacity: 1; }

	@keyframes cta-breath {
		0%, 100% { box-shadow: 0 0 6px rgba(61, 220, 132, 0.3),  inset 0 0 6px rgba(61, 220, 132, 0.1); }
		50%      { box-shadow: 0 0 22px rgba(61, 220, 132, 0.6), inset 0 0 14px rgba(61, 220, 132, 0.2); }
	}

	.cta-sub {
		font-size: 9px;
		color: var(--text-dim);
		letter-spacing: 2px;
	}

	@media (max-width: 900px) {
		.tac-root {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr auto auto;
		}
		.radar { width: min(70vw, 340px); }
	}
</style>
