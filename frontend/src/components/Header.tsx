import Image from "next/image";

import { APP_CONFIG } from "@/config/app";

/** Minimal branded top bar — logo links to configured marketing site. */
export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center px-8 py-4">
        <a
          href={APP_CONFIG.mainWebsiteUrl}
          target="_self"
          rel="noopener noreferrer"
          className="inline-flex shrink-0 rounded-sm outline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-gray-300"
        >
          <Image
            src={APP_CONFIG.logo}
            alt="MicroDegree"
            width={150}
            height={40}
            priority
            className="h-9 w-auto max-w-full object-contain object-left"
          />
        </a>
      </div>
    </header>
  );
}
