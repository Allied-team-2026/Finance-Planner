export default function VerificationBanner({ verifier }) {
  if (!verifier) return null

  // The verifier's own status field decides this, not our own re-reading of its
  // lists. If we judged pass/fail here we would be writing a second copy of the
  // verifier's rule, and the two copies would drift apart.
  const failed = verifier.status === 'fail'
  const retried = verifier.status === 'pass_after_retry'

  if (!failed) {
    return (
      <div className="rounded-xl bg-emerald-500/10 p-3 border border-emerald-500/20 flex items-center gap-3 text-xs text-emerald-200">
        <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <span>
          <strong>Verified against engine outputs:</strong> all {verifier.numbers_checked} numbers
          in the AI explanation match the deterministic engines
          {retried && ', after one regeneration'}.
        </span>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-rose-500/10 p-3 border border-rose-500/20 flex flex-col gap-2 text-xs text-rose-200">
      <div className="flex items-center gap-3">
        <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>
          <strong>Verification failed.</strong> The numbers in the plan tiles below come
          straight from the engines and are safe. Treat the written wording with caution.
        </span>
      </div>
      {verifier.unverified_numbers?.length > 0 && (
        <div className="ml-7 text-rose-300/80">
          Unverified: {verifier.unverified_numbers.join(', ')}
        </div>
      )}
      {verifier.suitability_flags?.length > 0 && (
        <div className="ml-7 text-rose-300/80">
          Flagged: {verifier.suitability_flags.join(', ')}
        </div>
      )}
    </div>
  )
}
