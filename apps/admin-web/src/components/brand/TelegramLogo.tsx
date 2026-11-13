/** El avión de papel de Telegram, para identificar el canal. Decorativo: el nombre va al lado en texto. */
export function TelegramLogo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        fill="currentColor"
        d="M21.94 3.35 2.98 10.66c-1.29.52-1.28 1.24-.23 1.56l4.86 1.52 1.87 5.73c.23.63.11.88.78.88.52 0 .75-.24 1.04-.52l2.43-2.36 5.06 3.74c.93.51 1.6.25 1.83-.86l3.32-15.64c.34-1.36-.52-1.98-1.4-1.58Zm-4.13 3.44-7.9 7.13-.31 3.28-1.46-4.77 9.3-5.86c.42-.26.82-.12.5.17Z"
      />
    </svg>
  );
}
