"use client";

import {
  type RefObject,
  useEffect,
  useRef,
} from "react";

export function useDialogFocus(
  open: boolean,
): RefObject<HTMLButtonElement | null> {
  const initialFocusRef =
    useRef<HTMLButtonElement | null>(null);

  const previousFocusRef =
    useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    previousFocusRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow = "hidden";

    const animationFrame =
      window.requestAnimationFrame(() => {
        initialFocusRef.current?.focus();
      });

    return () => {
      window.cancelAnimationFrame(animationFrame);

      document.body.style.overflow =
        previousOverflow;

      const previousFocus =
        previousFocusRef.current;

      if (
        previousFocus &&
        document.contains(previousFocus)
      ) {
        previousFocus.focus();
      }

      previousFocusRef.current = null;
    };
  }, [open]);

  return initialFocusRef;
}
