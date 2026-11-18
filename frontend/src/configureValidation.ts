import { config } from "zod";

// Configure validation before schemas initialize so Zod skips its eval probe under the deployed CSP.
config({ jitless: true });
