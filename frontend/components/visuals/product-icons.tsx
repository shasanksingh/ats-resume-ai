import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

export function ResumePrismIcon({ className = "h-8 w-8", ...props }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" aria-hidden="true" {...props}>
      <defs>
        <linearGradient id="resume-face" x1="14" y1="8" x2="49" y2="55" gradientUnits="userSpaceOnUse">
          <stop stopColor="#818CF8" />
          <stop offset="1" stopColor="#4338CA" />
        </linearGradient>
        <linearGradient id="resume-side" x1="45" y1="13" x2="56" y2="49" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22D3EE" />
          <stop offset="1" stopColor="#0E7490" />
        </linearGradient>
        <filter id="resume-shadow" x="4" y="4" width="56" height="58" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0" dy="5" stdDeviation="4" floodColor="#312E81" floodOpacity=".28" />
        </filter>
      </defs>
      <g filter="url(#resume-shadow)">
        <path d="M13 13.5 42 8l10 7.5v35L23 56l-10-7.5v-35Z" fill="url(#resume-face)" />
        <path d="m42 8 10 7.5-10 2.2V8Z" fill="#C7D2FE" />
        <path d="m42 17.7 10-2.2v35L42 53V17.7Z" fill="url(#resume-side)" />
        <path d="M21 23.5 36 21M21 31l15-2.5M21 38.5l11-2" stroke="white" strokeWidth="3" strokeLinecap="round" opacity=".9" />
      </g>
    </svg>
  );
}

export function MatchOrbitIcon({ className = "h-8 w-8", ...props }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" aria-hidden="true" {...props}>
      <defs>
        <radialGradient id="match-core" cx="0" cy="0" r="1" gradientTransform="translate(27 25) rotate(48) scale(27)">
          <stop stopColor="#67E8F9" />
          <stop offset=".58" stopColor="#6366F1" />
          <stop offset="1" stopColor="#312E81" />
        </radialGradient>
        <filter id="match-shadow" x="4" y="5" width="56" height="55" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0" dy="5" stdDeviation="4" floodColor="#312E81" floodOpacity=".25" />
        </filter>
      </defs>
      <g filter="url(#match-shadow)">
        <circle cx="30" cy="29" r="18" fill="url(#match-core)" />
        <path d="m23 29 5 5 10-12" stroke="white" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 36c5 13 33 17 44 3 7-9-2-21-15-25" stroke="#A5B4FC" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="51" cy="39" r="4" fill="#22D3EE" />
      </g>
    </svg>
  );
}

export function InsightStackIcon({ className = "h-8 w-8", ...props }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" aria-hidden="true" {...props}>
      <defs>
        <linearGradient id="stack-top" x1="13" y1="14" x2="50" y2="38" gradientUnits="userSpaceOnUse">
          <stop stopColor="#C4B5FD" />
          <stop offset="1" stopColor="#6366F1" />
        </linearGradient>
        <filter id="stack-shadow" x="5" y="6" width="54" height="54" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0" dy="5" stdDeviation="4" floodColor="#312E81" floodOpacity=".25" />
        </filter>
      </defs>
      <g filter="url(#stack-shadow)" strokeLinejoin="round">
        <path d="m10 38 22-12 22 12-22 13-22-13Z" fill="#164E63" stroke="#22D3EE" strokeWidth="2" />
        <path d="m10 29 22-12 22 12-22 13-22-13Z" fill="#4338CA" stroke="#A5B4FC" strokeWidth="2" />
        <path d="m10 20 22-12 22 12-22 13-22-13Z" fill="url(#stack-top)" stroke="#E0E7FF" strokeWidth="2" />
        <circle cx="32" cy="20" r="5" fill="white" opacity=".9" />
      </g>
    </svg>
  );
}

export function ExportCubeIcon({ className = "h-8 w-8", ...props }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" aria-hidden="true" {...props}>
      <defs>
        <linearGradient id="cube-left" x1="10" y1="24" x2="32" y2="54" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4F46E5" />
          <stop offset="1" stopColor="#312E81" />
        </linearGradient>
        <linearGradient id="cube-right" x1="33" y1="21" x2="52" y2="53" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22D3EE" />
          <stop offset="1" stopColor="#0E7490" />
        </linearGradient>
        <filter id="cube-shadow" x="5" y="5" width="54" height="55" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0" dy="5" stdDeviation="4" floodColor="#312E81" floodOpacity=".28" />
        </filter>
      </defs>
      <g filter="url(#cube-shadow)" strokeLinejoin="round">
        <path d="m10 20 22-12 22 12-22 13-22-13Z" fill="#A5B4FC" stroke="#E0E7FF" strokeWidth="2" />
        <path d="m10 20 22 13v23L10 43V20Z" fill="url(#cube-left)" stroke="#818CF8" strokeWidth="2" />
        <path d="m32 33 22-13v23L32 56V33Z" fill="url(#cube-right)" stroke="#67E8F9" strokeWidth="2" />
        <path d="M32 15v10m0 0-5-5m5 5 5-5" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </svg>
  );
}

export function CareerFlowIllustration({ className = "h-64 w-full", ...props }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 420 280" fill="none" aria-hidden="true" {...props}>
      <defs>
        <linearGradient id="career-panel" x1="84" y1="45" x2="315" y2="241" gradientUnits="userSpaceOnUse">
          <stop stopColor="#EEF2FF" />
          <stop offset="1" stopColor="#CFFAFE" />
        </linearGradient>
        <linearGradient id="career-card" x1="116" y1="67" x2="276" y2="210" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6366F1" />
          <stop offset="1" stopColor="#0891B2" />
        </linearGradient>
        <filter id="career-shadow" x="44" y="22" width="330" height="238" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0" dy="18" stdDeviation="18" floodColor="#312E81" floodOpacity=".22" />
        </filter>
      </defs>
      <g filter="url(#career-shadow)">
        <rect x="72" y="42" width="276" height="188" rx="34" fill="url(#career-panel)" />
        <rect x="105" y="70" width="128" height="142" rx="18" fill="white" />
        <rect x="126" y="96" width="64" height="9" rx="4.5" fill="#18181B" />
        <rect x="126" y="119" width="84" height="8" rx="4" fill="#A5B4FC" />
        <rect x="126" y="140" width="68" height="8" rx="4" fill="#C4B5FD" />
        <rect x="126" y="161" width="78" height="8" rx="4" fill="#67E8F9" />
        <rect x="126" y="184" width="54" height="8" rx="4" fill="#DDD6FE" />
        <rect x="250" y="82" width="64" height="64" rx="18" fill="url(#career-card)" />
        <path d="m266 115 15 15 24-31" stroke="white" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M95 235c47-40 88-26 122-52 37-29 26-78 93-96" stroke="#6366F1" strokeWidth="5" strokeLinecap="round" />
        <path d="M101 238c53-36 96-18 135-44 35-23 34-68 86-83" stroke="#22D3EE" strokeWidth="3" strokeLinecap="round" opacity=".8" />
        <circle cx="95" cy="235" r="9" fill="#6366F1" />
        <circle cx="322" cy="111" r="9" fill="#22D3EE" />
      </g>
    </svg>
  );
}
