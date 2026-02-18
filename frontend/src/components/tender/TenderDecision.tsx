import type { Tender, TenderDecision as Decision } from '../../types/tender'

interface TenderDecisionProps {
  tender: Tender
  decision: Decision
}

export default function TenderDecision({ tender, decision }: TenderDecisionProps) {
  const getDecisionColor = (dec: string | undefined) => {
    switch (dec) {
      case 'go': return 'text-green-600'
      case 'no_go': return 'text-red-600'
      case 'a_approfondir': return 'text-orange-600'
      default: return 'text-gray-600'
    }
  }

  const getDecisionBorder = (dec: string | undefined) => {
    switch (dec) {
      case 'go': return 'border-green-500 bg-green-50'
      case 'no_go': return 'border-red-500 bg-red-50'
      case 'a_approfondir': return 'border-orange-500 bg-orange-50'
      default: return 'border-gray-300 bg-gray-50'
    }
  }

  const getDecisionLabel = (dec: string | undefined) => {
    switch (dec) {
      case 'go': return 'GO'
      case 'no_go': return 'NO-GO'
      case 'a_approfondir': return 'A APPROFONDIR'
      default: return 'N/A'
    }
  }

  const isManualReview = tender.status === 'manual_review'

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Decision Go/No-Go</h3>

      {isManualReview ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-500 mb-2">Decision Systeme (Initiale)</p>
            <p className={`text-3xl font-bold ${getDecisionColor(decision.initial_decision)}`}>
              {getDecisionLabel(decision.initial_decision)}
            </p>
            {decision.initial_confidence != null && (
              <p className="text-sm text-gray-600 mt-2">
                Confiance: <span className="font-medium">{(decision.initial_confidence * 100).toFixed(1)}%</span>
              </p>
            )}
          </div>

          <div className={`border-2 rounded-lg p-4 ${
            decision.final_decision ? getDecisionBorder(decision.final_decision) : 'border-orange-300 bg-orange-50'
          }`}>
            <p className="text-sm font-medium text-gray-700 mb-2">Decision Finale (Reviewer)</p>
            {decision.final_decision ? (
              <>
                <p className={`text-3xl font-bold ${getDecisionColor(decision.final_decision)}`}>
                  {getDecisionLabel(decision.final_decision)}
                </p>
                {decision.final_decision_by_name && (
                  <p className="text-sm text-gray-700 mt-2">Par: {decision.final_decision_by_name}</p>
                )}
                {decision.final_decision_notes && (
                  <p className="text-xs text-gray-700 mt-2 italic">"{decision.final_decision_notes}"</p>
                )}
              </>
            ) : (
              <p className="text-lg text-orange-600 font-medium">En attente de revue...</p>
            )}
          </div>
        </div>
      ) : (
        <div className="mb-6">
          <div className={`border-2 rounded-lg p-6 ${getDecisionBorder(decision.initial_decision)}`}>
            <p className="text-sm font-medium text-gray-500 mb-2">Decision Systeme</p>
            <p className={`text-4xl font-bold ${getDecisionColor(decision.initial_decision)}`}>
              {getDecisionLabel(decision.initial_decision)}
            </p>
            {decision.initial_confidence != null && (
              <p className="text-sm text-gray-600 mt-2">
                Confiance: <span className="font-medium">{(decision.initial_confidence * 100).toFixed(1)}%</span>
              </p>
            )}
            {decision.win_probability_estimate != null && (
              <p className="text-sm text-gray-600 mt-1">
                Probabilite de gain: <span className="font-medium text-amber-700">{(decision.win_probability_estimate * 100).toFixed(1)}%</span>
              </p>
            )}
            {decision.estimated_margin_percentage != null && (
              <p className="text-sm text-gray-600 mt-1">
                Marge estimee: <span className="font-medium text-amber-700">{decision.estimated_margin_percentage.toFixed(1)}%</span>
              </p>
            )}
          </div>
        </div>
      )}

      {decision.risk_analysis && (
        <div className="mt-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3">Analyse des Risques</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {decision.risk_analysis.technical && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs font-semibold text-blue-800 mb-1">Technique</p>
                <p className="text-sm text-gray-700">{decision.risk_analysis.technical}</p>
              </div>
            )}
            {decision.risk_analysis.financial && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-xs font-semibold text-green-800 mb-1">Financier</p>
                <p className="text-sm text-gray-700">{decision.risk_analysis.financial}</p>
              </div>
            )}
            {decision.risk_analysis.resource && (
              <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-xs font-semibold text-purple-800 mb-1">Ressources</p>
                <p className="text-sm text-gray-700">{decision.risk_analysis.resource}</p>
              </div>
            )}
            {decision.risk_analysis.competition && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-xs font-semibold text-red-800 mb-1">Concurrence</p>
                <p className="text-sm text-gray-700">{decision.risk_analysis.competition}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {(decision.strengths?.length || decision.weaknesses?.length) ? (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {decision.strengths && decision.strengths.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="text-sm font-semibold text-green-800 mb-2">Points Forts</h4>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {decision.strengths.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          )}
          {decision.weaknesses && decision.weaknesses.length > 0 && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <h4 className="text-sm font-semibold text-red-800 mb-2">Points Faibles</h4>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {decision.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
        </div>
      ) : null}

      {decision.recommended_actions && decision.recommended_actions.length > 0 && (
        <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <h4 className="text-sm font-semibold text-amber-800 mb-2">Actions Recommandees</h4>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            {decision.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <p className="text-sm text-gray-600 mb-2">Raisonnement</p>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-gray-900 whitespace-pre-wrap">{decision.initial_reasoning || decision.reasoning || 'N/A'}</p>
        </div>
      </div>

      {decision.llm_model && (
        <div className="mt-4">
          <p className="text-sm text-gray-600">LLM Model: {decision.llm_model}</p>
        </div>
      )}
    </div>
  )
}
