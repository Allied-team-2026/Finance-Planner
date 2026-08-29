export default function VerificationBanner({ verifier }) {
  if (!verifier) return null

  const isVerified = verifier.unverified_numbers && verifier.unverified_numbers.length === 0

  if (isVerified) {
    return (
      <div className="rounded-xl bg-emerald-500/10 p-3 border border-emerald-500/20 flex items-center gap-3 text-xs text-emerald-200">
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <span>
          <strong>Verified against authoritative engine outputs:</strong> All AI-generated numbers perfectly match the deterministic backend engines.
        </span>
      </div>
    )
  } else {
    return (
      <div className="rounded-xl bg-rose-500/10 p-3 border border-rose-500/20 flex flex-col gap-2 text-xs text-rose-200">
        <div className="flex items-center gap-3">
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>
            <strong>Verification Failed:</strong> The AI explanation contains unverified numbers.
          </span>
        </div>
        {verifier.unverified_numbers && verifier.unverified_numbers.length > 0 && (
          <div className="ml-7 text-rose-300/80">
            Unverified numbers: {verifier.unverified_numbers.join(', ')}
          </div>
        )}
      </div>
    )
  }
}
