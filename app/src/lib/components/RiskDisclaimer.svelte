<script lang="ts">
	import { onMount } from 'svelte';

	const STORAGE_KEY = 'sentinel-risk-disclaimer-dismissed';
	let visible = true;

	onMount(() => {
		try {
			if (localStorage.getItem(STORAGE_KEY) === '1') visible = false;
		} catch {
			// localStorage may be blocked — keep banner shown
		}
	});

	function dismiss() {
		visible = false;
		try {
			localStorage.setItem(STORAGE_KEY, '1');
		} catch {
			// ignore
		}
	}
</script>

{#if visible}
	<div class="risk-banner" role="status" aria-live="polite">
		<div class="risk-banner-inner">
			<span class="risk-icon" aria-hidden>!</span>
			<span class="risk-text">
				<strong>SECURITY:</strong> signals are advisory, not financial advice. Devnet only.
			</span>
			<button class="risk-dismiss" on:click={dismiss} aria-label="Dismiss disclaimer">
				&times;
			</button>
		</div>
	</div>
{/if}

<style>
	.risk-banner {
		background: rgba(220, 60, 60, 0.08);
		border-bottom: 1px solid rgba(220, 60, 60, 0.4);
		padding: 8px 0;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 11px;
		letter-spacing: 0.4px;
	}
	.risk-banner-inner {
		max-width: 1280px;
		margin: 0 auto;
		padding: 0 24px;
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.risk-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		height: 16px;
		border: 1px solid rgba(220, 60, 60, 0.7);
		border-radius: 50%;
		color: rgba(220, 60, 60, 0.9);
		font-weight: 700;
		flex-shrink: 0;
	}
	.risk-text {
		color: rgba(220, 60, 60, 0.9);
		flex: 1;
	}
	.risk-text strong {
		color: rgba(255, 90, 90, 1);
		letter-spacing: 1px;
	}
	.risk-dismiss {
		background: transparent;
		border: 0;
		color: rgba(220, 60, 60, 0.7);
		cursor: pointer;
		font-size: 18px;
		line-height: 1;
		padding: 0 6px;
	}
	.risk-dismiss:hover {
		color: rgba(255, 120, 120, 1);
	}
</style>
