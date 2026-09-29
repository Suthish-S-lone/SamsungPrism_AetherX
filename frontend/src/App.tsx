import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { QueryInput } from './components/QueryInput';
import { LoadingState } from './components/LoadingState';
import { DiagnosisCard } from './components/DiagnosisCard';
import { GuidedWorkflow } from './components/GuidedWorkflow';
import { SimulatedSetting } from './components/SimulatedSetting';
import { ResolutionFeedback } from './components/ResolutionFeedback';
import { OutOfScopeView } from './components/OutOfScopeView';
import { ErrorView } from './components/ErrorView';
import { DebugPanel } from './components/DebugPanel';
import { troubleshootQuery, checkBackendHealth } from './services/api';
import type { Action, Context, StructuredTroubleshootResponse } from './types/api';

type AppStep = 'input' | 'loading' | 'diagnosis' | 'workflow' | 'feedback' | 'out_of_scope' | 'error';

export const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<AppStep>('input');
  const [currentQuery, setCurrentQuery] = useState('');
  const [backendOnline, setBackendOnline] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // API Response state
  const [apiResponse, setApiResponse] = useState<StructuredTroubleshootResponse | null>(null);
  const [activeContext, setActiveContext] = useState<Context | null>(null);

  // Workflow progress state
  const [currentActionIndex, setCurrentActionIndex] = useState(0);
  const [completedActions, setCompletedActions] = useState<number[]>([]);
  const [activeSimulatedAction, setActiveSimulatedAction] = useState<Action | null>(null);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  const handleDiagnose = async (queryText: string) => {
    setCurrentQuery(queryText);
    setCurrentStep('loading');
    setErrorMessage('');

    try {
      const response = await troubleshootQuery(queryText, true);
      setApiResponse(response);
      setBackendOnline(true);

      if (response.contexts && response.contexts.length > 0) {
        setActiveContext(response.contexts[0]);
        setCurrentActionIndex(0);
        setCompletedActions([]);
        setCurrentStep('diagnosis');
      } else {
        // Out of scope or no confident match
        setActiveContext(null);
        setCurrentStep('out_of_scope');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to connect to diagnostic backend.');
      setBackendOnline(false);
      setCurrentStep('error');
    }
  };

  const handleStartWorkflow = () => {
    setCurrentActionIndex(0);
    setCompletedActions([]);
    setCurrentStep('workflow');
  };

  const handleOpenDeeplink = (action: Action) => {
    setActiveSimulatedAction(action);
  };

  const handleMarkSettingChecked = () => {
    if (!completedActions.includes(currentActionIndex)) {
      setCompletedActions([...completedActions, currentActionIndex]);
    }
  };

  const handleCompleteAction = (actionIdx: number) => {
    if (!completedActions.includes(actionIdx)) {
      setCompletedActions([...completedActions, actionIdx]);
    }

    if (activeContext && actionIdx < activeContext.actions.length - 1) {
      setCurrentActionIndex(actionIdx + 1);
    }
  };

  const handleFinishWorkflow = () => {
    setCurrentStep('feedback');
  };

  const handleNewDiagnosis = () => {
    setCurrentQuery('');
    setApiResponse(null);
    setActiveContext(null);
    setCurrentActionIndex(0);
    setCompletedActions([]);
    setActiveSimulatedAction(null);
    setCurrentStep('input');
  };

  return (
    <div className="app-container">
      <Header
        backendOnline={backendOnline}
        debugMode={debugMode}
        onToggleDebug={() => setDebugMode(!debugMode)}
        onNewDiagnosis={handleNewDiagnosis}
      />

      <main className="main-content">
        {currentStep === 'input' && (
          <QueryInput onSubmit={handleDiagnose} isLoading={false} />
        )}

        {currentStep === 'loading' && (
          <LoadingState query={currentQuery} />
        )}

        {currentStep === 'diagnosis' && activeContext && (
          <DiagnosisCard
            context={activeContext}
            debugInfo={apiResponse?.debug_info}
            onStartWorkflow={handleStartWorkflow}
          />
        )}

        {currentStep === 'workflow' && activeContext && (
          <GuidedWorkflow
            context={activeContext}
            currentActionIndex={currentActionIndex}
            completedActions={completedActions}
            onOpenDeeplink={handleOpenDeeplink}
            onCompleteAction={handleCompleteAction}
            onFinishWorkflow={handleFinishWorkflow}
            onBackToDiagnosis={() => setCurrentStep('diagnosis')}
          />
        )}

        {currentStep === 'feedback' && activeContext && (
          <ResolutionFeedback
            context={activeContext}
            onNewDiagnosis={handleNewDiagnosis}
            onRetryDiagnosis={() => setCurrentStep('input')}
          />
        )}

        {currentStep === 'out_of_scope' && (
          <OutOfScopeView
            query={currentQuery}
            fallbackMessage={apiResponse?.fallback}
            onTryAgain={() => setCurrentStep('input')}
            onSelectSupportedExample={(ex) => handleDiagnose(ex)}
          />
        )}

        {currentStep === 'error' && (
          <ErrorView
            errorMessage={errorMessage}
            onRetry={() => handleDiagnose(currentQuery || 'My battery drains quickly')}
          />
        )}

        {/* Simulated Mobile Setting Modal */}
        {activeSimulatedAction && (
          <SimulatedSetting
            action={activeSimulatedAction}
            onClose={() => setActiveSimulatedAction(null)}
            onMarkChecked={handleMarkSettingChecked}
          />
        )}

        {/* Technical Diagnostics Inspector */}
        <DebugPanel
          debugInfo={apiResponse?.debug_info}
          isOpen={debugMode}
          onToggle={() => setDebugMode(!debugMode)}
        />
      </main>
    </div>
  );
};

export default App;
