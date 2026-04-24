import { Buffer } from 'buffer';

if (typeof window !== 'undefined') {
	const w = window as any;
	if (!w.Buffer) w.Buffer = Buffer;
	if (!w.global) w.global = window;
	if (!w.process) w.process = { env: {} };
}
