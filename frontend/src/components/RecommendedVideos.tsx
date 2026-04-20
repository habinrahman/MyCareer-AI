import React, { useMemo } from "react";
import { Video } from "lucide-react";
import { DEFAULT_PLAYLISTS, microdegreePlaylists } from "@/data/microdegreePlaylists";

interface Props {
  roles?: string[];
}

function roleMatchesCategory(role: string, category: string) {
  const r = role.trim().toLowerCase();
  const c = category.trim().toLowerCase();
  if (!r || !c) return false;
  return r === c || r.includes(c) || c.includes(r);
}

function playlistsForRoles(roles: string[]) {
  const cleaned = roles.map((r) => r.trim()).filter(Boolean);
  if (!cleaned.length) return DEFAULT_PLAYLISTS.slice(0, 6);

  const matched = microdegreePlaylists.filter((playlist) => {
    if (playlist.category === "General") return false;
    return cleaned.some((role) => roleMatchesCategory(role, playlist.category));
  });

  const playlists = matched.length ? matched : DEFAULT_PLAYLISTS;
  return playlists.slice(0, 6);
}

const RecommendedVideos: React.FC<Props> = ({ roles = [] }) => {
  const playlists = useMemo(() => playlistsForRoles(roles), [roles]);

  return (
    <div className="mt-10 border-t border-gray-100 pt-6">
      <div className="mb-4 flex items-center gap-2">
        <Video className="h-4 w-4 text-microRed" aria-hidden />
        <h3 className="text-xs font-bold uppercase tracking-wide text-microMuted">
          Recommended learning videos — MicroDegree
        </h3>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {playlists.map((playlist) => (
          <a
            key={`${playlist.category}-${playlist.title}`}
            href={playlist.url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-micro-lg border border-gray-100 bg-white p-5 shadow-micro transition hover:shadow-micro-lg"
          >
            <h4 className="text-sm font-semibold text-microText">{playlist.title}</h4>
            <p className="mt-2 text-xs text-microLight">MicroDegree YouTube playlist</p>
          </a>
        ))}
      </div>
    </div>
  );
};

export default RecommendedVideos;
