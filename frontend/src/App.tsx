import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import type { NavTab } from './components/Navbar';
import { AuthModal } from './components/AuthModal';
import { SettingsModal } from './components/SettingsModal';
import { GeneratorPage } from './pages/GeneratorPage';
import { StudioEditorPage } from './pages/StudioEditorPage';
import { LibraryPage } from './pages/LibraryPage';
import { InboxPage } from './pages/InboxPage';
import { StylePersonaPage } from './pages/StylePersonaPage';
import { settingsApi } from './api/client';
import { useDraftStore } from './store/useDraftStore';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('generator');
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Editor transfer state
  const [editorCreationId, setEditorCreationId] = useState<string | undefined>();
  const [editorDraftContent, setEditorDraftContent] = useState<string>('');
  const [editorTopic, setEditorTopic] = useState<string>('');

  useEffect(() => {
    // Initial fetch of configured studio model to sync draft store
    settingsApi
      .getSettings()
      .then((s) => {
        if (s?.default_model) {
          useDraftStore.getState().updateDefaultModel(s.default_model);
        }
      })
      .catch(() => {});

    const handleUnauthorized = () => {
      setIsAuthOpen(true);
    };
    const handleNavigate = (e: Event) => {
      const customEvent = e as CustomEvent<NavTab>;
      if (customEvent.detail) {
        setCurrentTab(customEvent.detail);
      }
    };

    window.addEventListener('pactory:unauthorized', handleUnauthorized);
    window.addEventListener('pactory:navigate', handleNavigate);
    return () => {
      window.removeEventListener('pactory:unauthorized', handleUnauthorized);
      window.removeEventListener('pactory:navigate', handleNavigate);
    };
  }, []);

  const handleOpenEditor = (creationId?: string, initialDraft?: string, topic?: string) => {
    setEditorCreationId(creationId);
    if (initialDraft !== undefined) setEditorDraftContent(initialDraft);
    if (topic !== undefined) setEditorTopic(topic);
    setCurrentTab('editor');
  };

  const handleOpenCreationFromLibrary = (creationId: string) => {
    setEditorCreationId(creationId);
    setEditorDraftContent('');
    setEditorTopic('');
    setCurrentTab('editor');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        onOpenAuth={() => setIsAuthOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className="flex-1">
        {currentTab === 'generator' && <GeneratorPage onOpenEditor={handleOpenEditor} />}
        {currentTab === 'editor' && (
          <StudioEditorPage
            initialCreationId={editorCreationId}
            initialDraftContent={editorDraftContent}
            initialTopic={editorTopic}
          />
        )}
        {currentTab === 'library' && (
          <LibraryPage onOpenCreation={handleOpenCreationFromLibrary} />
        )}
        {currentTab === 'inbox' && <InboxPage />}
        {currentTab === 'style' && <StylePersonaPage />}
      </main>

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={() => {}}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}

export default App;
