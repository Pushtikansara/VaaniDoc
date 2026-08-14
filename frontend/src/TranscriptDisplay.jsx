/* Transcript Display Component for VaaniDoc
Shows the original patient statement and English translation with safety verification status.

Follows existing VaaniDoc UI design (Tailwind CSS, panel component conventions).
Never hides the original statement. Clearly labels English as AI-generated translation.
Makes warnings visually obvious. Doctor remains the final clinical reviewer.
*/

import { useState } from "react";

/* Props for the TranscriptDisplay component */
interface TranscriptDisplayProps {
  /** The original Indian-language patient statement */
  originalText: string;

  /** The English translation (AI-generated) */
  englishText: string;

  /** Translation verification status from the safety checker */
  verificationStatus: "consistent" | "needs_review";

  /** Warning messages from the safety checker */
  warnings: Array<{ type: string; message: string }>;

  /** Callback when the doctor wants to review/edit */
  onReview?: () => void;

  /** Callback when the doctor wants to copy/export data */
  onCopy?: () => void;
}

/** TranscriptDisplay - Shows original + English translation with safety status */
export default function TranscriptDisplay({
  originalText,
  englishText,
  verificationStatus,
  warnings,
  onReview,
  onCopy,
}: TranscriptDisplayProps) {
  const [showWarnings, setShowWarnings] = useState(false);

  const hasWarnings = warnings && warnings.length > 0;

  /* Toggle warning visibility */
  const toggleWarnings = () => setShowWarnings(!showWarnings);

  /* Get status label and visual class */
  const getStatusInfo = () => {
    if (verificationStatus === "consistent") {
      return {
        label: "✓ No detected critical mismatch",
        className: "success",
        accent: "green",
      };
    }
    return {
      label: "⚠️ Translation needs review",
      className: "warning",
      accent: "red",
    };
  };

  const { label, className, accent } = getStatusInfo();

  /* Warning messages HTML */
  const warningItems = hasWarnings
    ? warnings.map(
        (w, i) => /* border-top py-2 */
      `
        <div className="pb-2 border-t border-gray-200 last:border-0">
          <p className="text-sm text-gray-600">${w.message}</p>
        </div>
      `
      )
    : [];

  return (
    <div className="space-y-4">
      {/* Original Patient Statement - ALWAYS visible */}
      <div className="panel p-4 border-t border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-2">Original Patient Statement</h3>
        <p className="text-lg text-gray-800 whitespace-pre-wrap">{originalText}</p>
        <p className="text-xs text-gray-500 mt-1">
          {"Original statement preserved as source/reference. "} AI-generated translation below.
        </p>
      </div>

      {/* English Translation - AI-generated */}
      <div className="panel p-4 border-t border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-2">AI-Generated English Translation</h3>
        <p className="text-lg text-gray-800 whitespace-pre-wrap">{englishText}</p>
        <p className="text-xs text-gray-500 mt-1">
          {"AI-generated translation for doctor's reference. "} Doctor remains the final clinical reviewer.
        </p>
      </div>

      {/* Translation Check Status */}
      <div className="panel p-4">
        <h3 className="font-semibold text-gray-900 mb-2">Translation Check</h3>
        <div className={`flex items-center space-x-2 ${accent}-500`}>
          <span className="icon">{label}</span>
          <span className="text-sm font-medium text-gray-800">{label}</span>
        </div>
        {hasWarnings && (
          <button
            onClick={toggleWarnings}
            className="text-sm text-gray-600 hover:text-gray-500 ml-auto"
          >
            {showWarnings ? "Hide warnings" : "Show warnings"}
          </button>
        )}
        {showWarnings && <div className="mt-2">{warningItems}</div>}
      </div>

      {/* Action buttons */}
      <div className="flex justify-end space-x-2">
        {onReview && (
          <button
            onClick={onReview}
            className="btn"
          >
            Review in EHR
          </button>
        )}
        {onCopy && (
          <button
            onClick={onCopy}
            className="btn"
          >
            Copy
          </button>
        )}
      </div>
    </div>
  );
}

export { TranscriptDisplay };