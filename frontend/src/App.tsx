import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { LandingView } from './components/LandingView';
import { QueryInput } from './components/QueryInput';
import { LoadingState } from './components/LoadingState';
import { ClarificationView } from './components/ClarificationView';
import { DiagnosisCard } from './components/DiagnosisCard';
import { GuidedWorkflow } from './components/GuidedWorkflow';
import { SimulatedSetting } from './components/SimulatedSetting';
import { ResolutionFeedback } from './components/ResolutionFeedback';
import { OutOfScopeView } from './components/OutOfScopeView';
import { ErrorView } from './components/ErrorView';
import { troubleshootQuery, continueTroubleshoot, checkBackendHealth } from './services/api';
import type { Action, ClarificationOption, Context, StructuredTroubleshootResponse } from './types/api';

type AppStep = 'landing' | 'input' | 'loading' | 'clarification' | 'diagnosis' | 'workflow' | 'feedback' | 'out_of_scope' | 'error';

export const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<AppStep>('landing');
  const [currentQuery, setCurrentQuery] = useState('');
  const [backendOnline, setBackendOnline] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [isClarifying, setIsClarifying] = useState(false);

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

      if (response.status === 'clarification_required' && response.clarification) {
        setActiveContext(null);
        setCurrentStep('clarification');
      } else if (response.contexts && response.contexts.length > 0) {
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
      setErrorMessage(err.message || 'Failed to connect to SmartGuide.');
      setBackendOnline(false);
      setCurrentStep('error');
    }
  };

  const handleSelectClarificationOption = async (option: ClarificationOption) => {
    if (!apiResponse?.session_id) return;
    setIsClarifying(true);
    setErrorMessage('');

    try {
      const response = await continueTroubleshoot(
        apiResponse.session_id,
        apiResponse.clarification?.id,
        option.id,
        null,
        true
      );
      setApiResponse(response);

      if (response.contexts && response.contexts.length > 0) {
        setActiveContext(response.contexts[0]);
        setCurrentActionIndex(0);
        setCompletedActions([]);
        setCurrentStep('diagnosis');
      } else {
        setActiveContext(null);
        setCurrentStep('out_of_scope');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to refine diagnosis.');
      setCurrentStep('error');
    } finally {
      setIsClarifying(false);
    }
  };

  const handleSubmitCustomClarification = async (customText: string) => {
    if (!apiResponse?.session_id) return;
    setIsClarifying(true);
    setErrorMessage('');

    try {
      const response = await continueTroubleshoot(
        apiResponse.session_id,
        apiResponse.clarification?.id,
        null,
        customText,
        true
      );
      setApiResponse(response);

      if (response.contexts && response.contexts.length > 0) {
        setActiveContext(response.contexts[0]);
        setCurrentActionIndex(0);
        setCompletedActions([]);
        setCurrentStep('diagnosis');
      } else {
        setActiveContext(null);
        setCurrentStep('out_of_scope');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to refine diagnosis.');
      setCurrentStep('error');
    } finally {
      setIsClarifying(false);
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

  const handleStartTroubleshooting = () => {
    setCurrentStep('input');
  };

  const handleGoHome = () => {
    setCurrentQuery('');
    setApiResponse(null);
    setActiveContext(null);
    setCurrentActionIndex(0);
    setCompletedActions([]);
    setActiveSimulatedAction(null);
    setCurrentStep('landing');
  };

  // Show header only when past the landing screen
  const showHeader = currentStep !== 'landing';

  return (
    <div className="app-container">
      {showHeader && <Header onNewDiagnosis={handleNewDiagnosis} />}

      <main className={`main-content ${currentStep === 'landing' ? 'landing-main' : ''}`}>
        {currentStep === 'landing' && (
          <LandingView
            onStartTroubleshooting={handleStartTroubleshooting}
            onQuickCategory={handleDiagnose}
            onTryExample={handleDiagnose}
          />
        )}

        {currentStep === 'input' && (
          <QueryInput onSubmit={handleDiagnose} isLoading={false} />
        )}

        {currentStep === 'loading' && (
          <LoadingState query={currentQuery} />
        )}

        {currentStep === 'clarification' && apiResponse?.clarification && (
          <ClarificationView
            clarification={apiResponse.clarification}
            isLoading={isClarifying}
            onSelectOption={handleSelectClarificationOption}
            onSubmitCustom={handleSubmitCustomClarification}
            onCancel={handleNewDiagnosis}
          />
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
      </main>
    </div>
  );
};

export default App;
