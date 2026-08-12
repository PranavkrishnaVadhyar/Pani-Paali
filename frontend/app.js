/* ==========================================================================
   PANI PAALI - MAIN APPLICATION LOGIC
   Vanilla JavaScript SPA implementation
   ========================================================================== */

(function () {
  'use strict';

  // =========================================================================
  // STATE MANAGEMENT
  // =========================================================================
  let state = {
    apiBaseUrl: localStorage.getItem('pani_paali_api_url') || 'https://pani-paali-2.onrender.com',
    currentView: 'landingView', // landingView | formView | trackerView
    currentStep: 1, // 1 | 2 | 3 | 4
    
    // Form Inputs
    prankType: 'meme_soundboard', // meme_soundboard | hiring_manager | movie_spoiler
    contactName: '',
    contactPhone: '',
    
    // Hiring Manager Specific
    hiringRole: '',
    hiringInterviewer: '',
    hiringCompany: '',
    hiringExtra: '',
    
    // Movie Spoiler Specific
    movieTitle: '',
    movieNotes: '',
    movieCustomStory: '',
    
    // AI Preview Data
    firstMessage: '',
    systemPrompt: '',
    
    // Live Call Tracking
    currentCallId: null,
    pollInterval: null,
    isSubmittingCall: false
  };

  // =========================================================================
  // DOM ELEMENT REFERENCES
  // =========================================================================
  const dom = {
    // Header & Health
    healthBadge: document.getElementById('healthBadge'),
    healthDot: document.getElementById('healthDot'),
    healthText: document.getElementById('healthText'),
    settingsBtn: document.getElementById('settingsBtn'),
    logoLink: document.getElementById('logoLink'),
    
    // Views
    landingView: document.getElementById('landingView'),
    formView: document.getElementById('formView'),
    trackerView: document.getElementById('trackerView'),
    
    // Landing CTA
    startPrankBtn: document.getElementById('startPrankBtn'),
    
    // Form & Stepper
    prankForm: document.getElementById('prankForm'),
    progressBarFill: document.getElementById('progressBarFill'),
    nodes: [
      document.getElementById('node1'),
      document.getElementById('node2'),
      document.getElementById('node3'),
      document.getElementById('node4')
    ],
    steps: [
      document.getElementById('step1'),
      document.getElementById('step2'),
      document.getElementById('step3'),
      document.getElementById('step4')
    ],
    errorBox: document.getElementById('errorBox'),
    errorMessage: document.getElementById('errorMessage'),
    
    // Inputs
    optionCards: document.querySelectorAll('.option-card'),
    contactNameInput: document.getElementById('contactName'),
    contactPhoneInput: document.getElementById('contactPhone'),
    
    // Step 3 Prank Containers
    step3Title: document.getElementById('step3Title'),
    fieldsMemeSoundboard: document.getElementById('fieldsMemeSoundboard'),
    fieldsHiringManager: document.getElementById('fieldsHiringManager'),
    fieldsMovieSpoiler: document.getElementById('fieldsMovieSpoiler'),
    
    // Hiring Inputs
    hiringRoleInput: document.getElementById('hiringRole'),
    hiringInterviewerInput: document.getElementById('hiringInterviewer'),
    hiringCompanyInput: document.getElementById('hiringCompany'),
    hiringExtraInput: document.getElementById('hiringExtra'),
    
    // Movie Inputs
    movieTitleInput: document.getElementById('movieTitle'),
    movieNotesInput: document.getElementById('movieNotes'),
    movieCustomStoryInput: document.getElementById('movieCustomStory'),
    
    // Step 4 Preview Elements
    previewLoader: document.getElementById('previewLoader'),
    previewContent: document.getElementById('previewContent'),
    firstMessageInput: document.getElementById('firstMessage'),
    systemPromptInput: document.getElementById('systemPrompt'),
    regenerateBtn: document.getElementById('regenerateBtn'),
    
    // Stepper Navigation Buttons
    prevStepBtn: document.getElementById('prevStepBtn'),
    nextStepBtn: document.getElementById('nextStepBtn'),
    
    // Tracker View Elements
    radarContainer: document.getElementById('radarContainer'),
    trackerHeadline: document.getElementById('trackerHeadline'),
    trackerSubhead: document.getElementById('trackerSubhead'),
    callStatusPill: document.getElementById('callStatusPill'),
    callStatusText: document.getElementById('callStatusText'),
    detailCallId: document.getElementById('detailCallId'),
    detailContact: document.getElementById('detailContact'),
    detailPrankType: document.getElementById('detailPrankType'),
    rowSuccessEval: document.getElementById('rowSuccessEval'),
    detailSuccessEval: document.getElementById('detailSuccessEval'),
    callResultsContainer: document.getElementById('callResultsContainer'),
    summaryBoxSection: document.getElementById('summaryBoxSection'),
    summaryContent: document.getElementById('summaryContent'),
    transcriptBoxSection: document.getElementById('transcriptBoxSection'),
    transcriptContent: document.getElementById('transcriptContent'),
    recordingBoxSection: document.getElementById('recordingBoxSection'),
    audioPlayer: document.getElementById('audioPlayer'),
    trackerErrorBox: document.getElementById('trackerErrorBox'),
    trackerErrorText: document.getElementById('trackerErrorText'),
    resetFlowBtn: document.getElementById('resetFlowBtn'),
    
    // Opt-Out Modal Elements
    triggerOptOutModal: document.getElementById('triggerOptOutModal'),
    optOutModal: document.getElementById('optOutModal'),
    closeOptOutBtn: document.getElementById('closeOptOutBtn'),
    optOutForm: document.getElementById('optOutForm'),
    optOutPhoneInput: document.getElementById('optOutPhone'),
    optOutReasonInput: document.getElementById('optOutReason'),
    optOutErrorBox: document.getElementById('optOutErrorBox'),
    optOutErrorText: document.getElementById('optOutErrorText'),
    submitOptOutBtn: document.getElementById('submitOptOutBtn'),
    
    // Settings Modal Elements
    settingsModal: document.getElementById('settingsModal'),
    closeSettingsBtn: document.getElementById('closeSettingsBtn'),
    apiBaseUrlInput: document.getElementById('apiBaseUrlInput'),
    saveSettingsBtn: document.getElementById('saveSettingsBtn')
  };

  // =========================================================================
  // INITIALIZATION & EVENT LISTENERS
  // =========================================================================
  function init() {
    // Set API Base URL field value
    dom.apiBaseUrlInput.value = state.apiBaseUrl;
    
    // Health check on startup
    checkBackendHealth();
    setInterval(checkBackendHealth, 15000);
    
    // Event Handlers Setup
    setupEventListeners();
  }

  function setupEventListeners() {
    // Navigation / Header
    dom.logoLink.addEventListener('click', (e) => {
      e.preventDefault();
      switchView('landingView');
    });
    
    dom.startPrankBtn.addEventListener('click', () => {
      switchView('formView');
      goToStep(1);
    });
    
    // Prank Type Selection (Step 1)
    dom.optionCards.forEach((card) => {
      card.addEventListener('click', () => selectPrankType(card.dataset.value));
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          selectPrankType(card.dataset.value);
        }
      });
    });
    
    // Stepper Navigation
    dom.prevStepBtn.addEventListener('click', handlePrevStep);
    dom.nextStepBtn.addEventListener('click', handleNextStep);
    
    // Regenerate Script Button
    dom.regenerateBtn.addEventListener('click', fetchPreviewScript);
    
    // Reset Flow Button
    dom.resetFlowBtn.addEventListener('click', () => {
      stopPolling();
      switchView('formView');
      goToStep(1);
    });
    
    // Opt-Out Modal Triggers
    dom.triggerOptOutModal.addEventListener('click', () => openModal(dom.optOutModal));
    dom.closeOptOutBtn.addEventListener('click', () => closeModal(dom.optOutModal));
    dom.optOutForm.addEventListener('submit', handleOptOutSubmit);
    
    // Settings Modal Triggers
    dom.settingsBtn.addEventListener('click', () => openModal(dom.settingsModal));
    dom.closeSettingsBtn.addEventListener('click', () => closeModal(dom.settingsModal));
    dom.saveSettingsBtn.addEventListener('click', handleSaveSettings);
  }

  // =========================================================================
  // BACKEND HEALTH CHECK API
  // =========================================================================
  async function checkBackendHealth() {
    try {
      const response = await fetch(`${getCleanApiUrl()}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      if (response.ok) {
        dom.healthDot.className = 'status-dot online';
        dom.healthText.textContent = 'Server Online';
      } else {
        throw new Error('Health check returned non-200');
      }
    } catch (err) {
      dom.healthDot.className = 'status-dot offline';
      dom.healthText.textContent = 'Server Offline';
    }
  }

  function getCleanApiUrl() {
    return state.apiBaseUrl.replace(/\/+$/, '');
  }

  // =========================================================================
  // VIEW & STEP SWITCHING LOGIC
  // =========================================================================
  function switchView(viewId) {
    state.currentView = viewId;
    [dom.landingView, dom.formView, dom.trackerView].forEach((v) => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function selectPrankType(type) {
    state.prankType = type;
    dom.optionCards.forEach((card) => {
      const isSelected = card.dataset.value === type;
      card.classList.toggle('selected', isSelected);
      card.setAttribute('aria-checked', isSelected ? 'true' : 'false');
    });
    renderStep3Fields();
  }

  function renderStep3Fields() {
    dom.fieldsMemeSoundboard.style.display = 'none';
    dom.fieldsHiringManager.style.display = 'none';
    dom.fieldsMovieSpoiler.style.display = 'none';

    if (state.prankType === 'meme_soundboard') {
      dom.step3Title.textContent = 'Step 3 — Meme Soundboard Settings';
      dom.fieldsMemeSoundboard.style.display = 'block';
    } else if (state.prankType === 'hiring_manager') {
      dom.step3Title.textContent = 'Step 3 — Job Interview Details';
      dom.fieldsHiringManager.style.display = 'block';
    } else if (state.prankType === 'movie_spoiler') {
      dom.step3Title.textContent = 'Step 3 — Movie Spoiler Details';
      dom.fieldsMovieSpoiler.style.display = 'block';
    }
  }

  function goToStep(stepNum) {
    hideError();
    const oldStepNum = state.currentStep;
    state.currentStep = stepNum;

    // Update Progress Bar & Stepper Nodes
    const progressPct = ((stepNum - 1) / 3) * 100 + 25;
    dom.progressBarFill.style.width = `${progressPct}%`;

    dom.nodes.forEach((node, idx) => {
      const nNum = idx + 1;
      node.classList.remove('active', 'completed');
      if (nNum === stepNum) {
        node.classList.add('active');
      } else if (nNum < stepNum) {
        node.classList.add('completed');
      }
    });

    // Show correct Step panel with smooth fade transition
    const activeStepEl = dom.steps.find((s, idx) => idx + 1 === oldStepNum);
    const newStepEl = dom.steps.find((s, idx) => idx + 1 === stepNum);

    if (activeStepEl && activeStepEl !== newStepEl && activeStepEl.classList.contains('active')) {
      activeStepEl.classList.add('fading-out');
      setTimeout(() => {
        activeStepEl.classList.remove('active', 'fading-out');
        newStepEl.classList.add('active');
        newStepEl.classList.add('fading-in');
        setTimeout(() => {
          newStepEl.classList.remove('fading-in');
        }, 200);
      }, 200);
    } else {
      dom.steps.forEach((s, idx) => {
        s.classList.toggle('active', idx + 1 === stepNum);
        s.classList.remove('fading-out', 'fading-in');
      });
    }

    // Handle Button states
    dom.prevStepBtn.style.visibility = stepNum > 1 ? 'visible' : 'hidden';

    if (stepNum === 4) {
      dom.nextStepBtn.innerHTML = '<span>Confirm & Call 🔥</span>';
    } else if (stepNum === 3 && state.prankType === 'meme_soundboard') {
      dom.nextStepBtn.innerHTML = '<span>Place Call 🔥</span>';
    } else {
      dom.nextStepBtn.innerHTML = '<span>Continue</span> →';
    }

    // Trigger AI preview fetching if entering Step 4
    if (stepNum === 4) {
      fetchPreviewScript();
    }
  }

  // =========================================================================
  // STEP NAVIGATION & VALIDATION
  // =========================================================================
  function handlePrevStep() {
    if (state.currentStep > 1) {
      goToStep(state.currentStep - 1);
    }
  }

  async function handleNextStep() {
    hideError();

    // Step 1 Validation
    if (state.currentStep === 1) {
      if (!state.prankType) {
        showError('Please select a prank type to continue.');
        return;
      }
      goToStep(2);
      return;
    }

    // Step 2 Validation
    if (state.currentStep === 2) {
      const name = dom.contactNameInput.value.trim();
      const phone = dom.contactPhoneInput.value.trim();

      if (!name) {
        showError('Please enter a recipient contact name.');
        dom.contactNameInput.focus();
        return;
      }

      // E.164 phone validation pattern: + followed by 7 to 15 digits
      const e164Regex = /^\+[1-9]\d{6,14}$/;
      if (!phone || !e164Regex.test(phone)) {
        showError('Please enter a valid phone number in E.164 format (e.g. +919876543210).');
        dom.contactPhoneInput.focus();
        return;
      }

      state.contactName = name;
      state.contactPhone = phone;
      goToStep(3);
      return;
    }

    // Step 3 Validation & Branching
    if (state.currentStep === 3) {
      if (state.prankType === 'hiring_manager') {
        state.hiringRole = dom.hiringRoleInput.value.trim();
        state.hiringInterviewer = dom.hiringInterviewerInput.value.trim();
        state.hiringCompany = dom.hiringCompanyInput.value.trim();
        state.hiringExtra = dom.hiringExtraInput.value.trim();
      } else if (state.prankType === 'movie_spoiler') {
        const title = dom.movieTitleInput.value.trim();
        if (!title) {
          showError('Movie Title is required for Movie Spoiler pranks.');
          dom.movieTitleInput.focus();
          return;
        }
        state.movieTitle = title;
        state.movieNotes = dom.movieNotesInput.value.trim();
        state.movieCustomStory = dom.movieCustomStoryInput.value.trim();
      }

      // Special handling: Skip step 4 entirely for meme_soundboard
      if (state.prankType === 'meme_soundboard') {
        await initiateCall();
      } else {
        goToStep(4);
      }
      return;
    }

    // Step 4 Final Confirmation Action
    if (state.currentStep === 4) {
      await initiateCall();
    }
  }

  // =========================================================================
  // API INTEGRATION 1: POST /api/calls/preview
  // =========================================================================
  async function fetchPreviewScript() {
    dom.previewLoader.style.display = 'flex';
    dom.previewContent.style.display = 'none';
    dom.nextStepBtn.disabled = true;

    const payload = {
      contact_name: state.contactName,
      prank_type: state.prankType
    };

    if (state.prankType === 'movie_spoiler') {
      payload.context = state.movieTitle;
      payload.movie_spoiler_input = {
        custom_notes: state.movieNotes || undefined,
        user_written_story: state.movieCustomStory || undefined
      };
    } else if (state.prankType === 'hiring_manager') {
      payload.hiring_manager_input = {
        role: state.hiringRole || undefined,
        interviewer_name: state.hiringInterviewer || undefined,
        company_name: state.hiringCompany || undefined,
        extra_instructions: state.hiringExtra || undefined
      };
    }

    try {
      const response = await fetch(`${getCleanApiUrl()}/api/calls/preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned status ${response.status}`);
      }

      const data = await response.json();
      state.firstMessage = data.first_message || '';
      state.systemPrompt = data.system_prompt || '';

      dom.firstMessageInput.value = state.firstMessage;
      dom.systemPromptInput.value = state.systemPrompt;

      dom.previewLoader.style.display = 'none';
      dom.previewContent.style.display = 'block';
    } catch (err) {
      dom.previewLoader.style.display = 'none';
      dom.previewContent.style.display = 'block';
      showError(`Failed to generate AI script preview: ${err.message}`);
    } finally {
      dom.nextStepBtn.disabled = false;
    }
  }

  // =========================================================================
  // API INTEGRATION 2: POST /api/calls
  // =========================================================================
  async function initiateCall() {
    if (state.isSubmittingCall) return;
    state.isSubmittingCall = true;

    setLoadingButton(dom.nextStepBtn, true);

    const payload = {
      contact_name: state.contactName,
      contact_phone: state.contactPhone,
      prank_type: state.prankType
    };

    if (state.prankType === 'movie_spoiler') {
      payload.context = state.movieTitle;
      payload.movie_spoiler_input = {
        custom_notes: state.movieNotes || undefined,
        user_written_story: state.movieCustomStory || undefined
      };
    } else if (state.prankType === 'hiring_manager') {
      payload.hiring_manager_input = {
        role: state.hiringRole || undefined,
        interviewer_name: state.hiringInterviewer || undefined,
        company_name: state.hiringCompany || undefined,
        extra_instructions: state.hiringExtra || undefined
      };
    }

    // Pass custom edited script from Step 4 if available
    if (state.currentStep === 4) {
      const editedFirst = dom.firstMessageInput.value.trim();
      const editedSystem = dom.systemPromptInput.value.trim();
      if (editedFirst) payload.first_message = editedFirst;
      if (editedSystem) payload.system_prompt = editedSystem;
    }

    try {
      const response = await fetch(`${getCleanApiUrl()}/api/calls`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('This number is on the Do-Not-Call (DNC) list. Call cannot be placed.');
        } else if (response.status === 400) {
          throw new Error('Missing required fields or invalid phone format.');
        } else if (response.status === 502) {
          throw new Error('Failed to initiate call service via provider.');
        }
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Call placement failed (${response.status})`);
      }

      const callData = await response.json();
      state.currentCallId = callData.id;

      // Switch to tracker view & start polling
      switchView('trackerView');
      updateTrackerUI(callData);
      startPolling(callData.id);

    } catch (err) {
      showError(err.message);
    } finally {
      state.isSubmittingCall = false;
      setLoadingButton(dom.nextStepBtn, false);
    }
  }

  // =========================================================================
  // API INTEGRATION 3: GET /api/calls/{id} STATUS POLLING
  // =========================================================================
  function startPolling(callId) {
    stopPolling();
    state.pollInterval = setInterval(() => pollCallStatus(callId), 3000);
  }

  function stopPolling() {
    if (state.pollInterval) {
      clearInterval(state.pollInterval);
      state.pollInterval = null;
    }
  }

  async function pollCallStatus(callId) {
    try {
      const response = await fetch(`${getCleanApiUrl()}/api/calls/${callId}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) return;

      const callData = await response.json();
      updateTrackerUI(callData);

      // Stop polling on final status states
      if (callData.status === 'completed' || callData.status === 'failed') {
        stopPolling();
      }
    } catch (err) {
      console.warn('Error polling call status:', err);
    }
  }

  function updateTrackerUI(call) {
    dom.detailCallId.textContent = call.id ? `${call.id.substring(0, 8)}...` : 'N/A';
    dom.detailContact.textContent = `${call.contact_name} (${call.contact_phone})`;
    dom.detailPrankType.textContent = formatPrankTypeName(call.prank_type);

    const status = (call.status || 'queued').toLowerCase();
    dom.callStatusPill.className = `status-pill ${status}`;
    dom.callStatusText.textContent = status.toUpperCase();

    // Radar Wave animation handling
    if (status === 'ringing' || status === 'in-progress' || status === 'queued') {
      dom.radarContainer.style.display = 'flex';
      dom.trackerHeadline.textContent = 'Pani vechu! Call ready 🔥';
      dom.trackerSubhead.textContent = `Call is currently ${status}...`;
    } else {
      dom.radarContainer.style.display = 'none';
    }

    // Success state
    if (status === 'completed') {
      dom.trackerHeadline.textContent = 'Pani complete aayi! 🎉';
      dom.trackerSubhead.textContent = 'The call has concluded successfully.';
      dom.trackerErrorBox.style.display = 'none';
      dom.callResultsContainer.style.display = 'block';

      // Evaluation
      if (call.success_evaluation) {
        dom.rowSuccessEval.style.display = 'flex';
        dom.detailSuccessEval.textContent = call.success_evaluation;
      }

      // Summary
      if (call.summary) {
        dom.summaryBoxSection.style.display = 'block';
        dom.summaryContent.textContent = call.summary;
      }

      // Transcript
      if (call.transcript) {
        dom.transcriptBoxSection.style.display = 'block';
        dom.transcriptContent.textContent = call.transcript;
      }

      // Audio Recording
      if (call.recording_url) {
        dom.recordingBoxSection.style.display = 'block';
        dom.audioPlayer.src = call.recording_url;
      }
    }

    // Failure state
    if (status === 'failed') {
      dom.trackerHeadline.textContent = 'Pani paali... Call failed ❌';
      dom.trackerSubhead.textContent = 'The prank call could not be completed.';
      dom.trackerErrorBox.style.display = 'flex';
      dom.trackerErrorText.textContent = call.error || call.ended_reason || 'Unknown call error occurred.';
    }
  }

  function formatPrankTypeName(type) {
    switch (type) {
      case 'meme_soundboard': return 'Meme Soundboard';
      case 'hiring_manager': return 'Fake Hiring Manager';
      case 'movie_spoiler': return 'Movie Spoiler';
      default: return type || 'Prank Call';
    }
  }

  // =========================================================================
  // API INTEGRATION 4: POST /api/contacts/opt-out
  // =========================================================================
  async function handleOptOutSubmit(e) {
    e.preventDefault();
    const phone = dom.optOutPhoneInput.value.trim();
    const reason = dom.optOutReasonInput.value.trim();

    dom.optOutErrorBox.style.display = 'none';
    const e164Regex = /^\+[1-9]\d{6,14}$/;
    if (!phone || !e164Regex.test(phone)) {
      showOptOutError('Please enter a valid phone number in E.164 format (e.g. +919876543210).');
      return;
    }

    setLoadingButton(dom.submitOptOutBtn, true);

    try {
      const response = await fetch(`${getCleanApiUrl()}/api/contacts/opt-out`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          phone: phone,
          reason: reason || undefined
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Opt-out submission failed (${response.status})`);
      }

      alert(`Phone number ${phone} successfully added to the Do-Not-Call (DNC) list.`);
      closeModal(dom.optOutModal);
      dom.optOutPhoneInput.value = '';
      dom.optOutReasonInput.value = '';
    } catch (err) {
      showOptOutError(err.message);
    } finally {
      setLoadingButton(dom.submitOptOutBtn, false);
    }
  }

  function showOptOutError(msg) {
    dom.optOutErrorBox.style.display = 'flex';
    dom.optOutErrorText.textContent = msg;
  }

  // =========================================================================
  // API BASE URL CONFIGURATION
  // =========================================================================
  function handleSaveSettings() {
    const url = dom.apiBaseUrlInput.value.trim();
    if (!url) return;
    state.apiBaseUrl = url;
    localStorage.setItem('pani_paali_api_url', url);
    closeModal(dom.settingsModal);
    checkBackendHealth();
  }

  // =========================================================================
  // UTILITIES & HELPERS
  // =========================================================================
  function showError(msg) {
    dom.errorMessage.textContent = msg;
    dom.errorBox.classList.add('visible');
    dom.errorBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function hideError() {
    dom.errorBox.classList.remove('visible');
  }

  function setLoadingButton(btn, isLoading) {
    if (isLoading) {
      btn.dataset.originalHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<div class="loading-spinner"></div>`;
    } else {
      btn.disabled = false;
      if (btn.dataset.originalHtml) {
        btn.innerHTML = btn.dataset.originalHtml;
      }
    }
  }

  function openModal(modalEl) {
    modalEl.classList.add('active');
  }

  function closeModal(modalEl) {
    modalEl.classList.remove('active');
  }

  // Initialize Application
  document.addEventListener('DOMContentLoaded', init);

})();
