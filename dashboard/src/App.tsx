import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import {
  getClaim,
  getClaims,
  getInstructions,
  payClaim,
  signOffClaim,
  startClaim,
} from "./api";
import { ClaimDetailPanel } from "./components/ClaimDetailPanel";
import { InstructionsPanel } from "./components/InstructionsPanel";
import { Queue } from "./components/Queue";
import type { ClaimDetail, QueueClaim } from "./types";

type View = "claims" | "instructions";

export function App() {
  const [claims, setClaims] = useState<QueueClaim[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ClaimDetail | null>(null);
  const [instructions, setInstructions] = useState("");
  const [view, setView] = useState<View>("claims");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async () => {
    const response = await getClaims();
    setClaims(response.claims);
    return response;
  }, []);

  const loadDetail = useCallback(async (claimId: string) => {
    setDetail(await getClaim(claimId));
  }, []);

  const refresh = useCallback(async () => {
    if (selectedId) await loadDetail(selectedId);
    await loadQueue();
  }, [loadDetail, loadQueue, selectedId]);

  useEffect(() => {
    async function load() {
      try {
        const [queue] = await Promise.all([
          loadQueue(),
          getInstructions().then((response) => {
            setInstructions(response.instructions);
          }),
        ]);
        const firstClaimId = queue.claims.at(0)?.claim_id ?? null;
        setSelectedId(firstClaimId);
        if (firstClaimId) await loadDetail(firstClaimId);
      } catch (loadError) {
        setError(
          loadError instanceof Error ? loadError.message : "Unable to load",
        );
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [loadDetail, loadQueue]);

  useEffect(() => {
    if (detail?.status !== "in_progress" || !selectedId) return;
    const timer = window.setInterval(() => {
      void refresh();
    }, 750);
    return () => {
      window.clearInterval(timer);
    };
  }, [detail?.status, refresh, selectedId]);

  const runAction = useCallback(
    async (action: () => Promise<unknown>) => {
      try {
        setBusy(true);
        setError(null);
        await action();
        await refresh();
      } catch (actionError) {
        setError(
          actionError instanceof Error ? actionError.message : "Action failed",
        );
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  const runSelected = () => {
    if (selectedId)
      void runAction(() => startClaim(selectedId, `web-${String(Date.now())}`));
  };
  const signOffSelected = () => {
    if (selectedId) void runAction(() => signOffClaim(selectedId, "HND-01"));
  };
  const paySelected = () => {
    if (selectedId && detail?.decision) {
      const payout = detail.decision.payout;
      void runAction(() => payClaim(selectedId, payout));
    }
  };

  const selectClaim = (claimId: string) => {
    setSelectedId(claimId);
    void loadDetail(claimId).catch((loadError: unknown) => {
      setError(
        loadError instanceof Error ? loadError.message : "Unable to load",
      );
    });
  };

  let content: ReactNode;
  if (view === "instructions") {
    content = <InstructionsPanel instructions={instructions} />;
  } else if (loading) {
    content = <main className="center-state">Loading claims…</main>;
  } else {
    content = (
      <main className="workspace">
        <Queue claims={claims} selectedId={selectedId} onSelect={selectClaim} />
        <ClaimDetailPanel
          detail={detail}
          busy={busy}
          onRun={runSelected}
          onSignOff={signOffSelected}
          onPay={paySelected}
        />
      </main>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Claims operations</p>
          <h1>UnderCover</h1>
        </div>
        <nav aria-label="Primary navigation">
          <button
            aria-current={view === "claims" ? "page" : undefined}
            onClick={() => {
              setView("claims");
            }}
          >
            Claims
          </button>
          <button
            aria-current={view === "instructions" ? "page" : undefined}
            onClick={() => {
              setView("instructions");
            }}
          >
            Agent instructions
          </button>
        </nav>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {content}
    </div>
  );
}
