import { act, renderHook } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { useArtPreferences } from "./useArtPreferences";

const key = "amk_art_preferences";
afterEach(() => localStorage.removeItem(key));

it.each([null, '{"artwork":"reflection"}', "invalid JSON"])("defaults sound on for %s", saved => {
  if (saved !== null) localStorage.setItem(key, saved);
  const { result } = renderHook(useArtPreferences);
  expect(result.current.preferences.sound).toBe(true);
});

it("remembers mute through a reload", () => {
  const first = renderHook(useArtPreferences);
  act(() => first.result.current.set("sound", false));
  first.unmount();
  expect(renderHook(useArtPreferences).result.current.preferences.sound).toBe(false);
});
