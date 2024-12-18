import { component$ } from '@builder.io/qwik';
import { type DocumentHead } from '@builder.io/qwik-city';
import { FileList } from '~/components/author/FileList';
import { KnowledgeGraph } from '~/components/author/KnowledgeGraph';
import { ContentViewer } from '~/components/author/ContentViewer';
import { NavBar } from '~/components/navigation/NavBar';

export default component$(() => {
  return (
    <div class="flex flex-col h-screen">
      <NavBar />
      <div class="flex-1 flex overflow-hidden">
        {/* Left sidebar - Section list */}
        <div class="w-64 bg-gray-50 border-r border-gray-200 flex flex-col overflow-y-auto">
          <div class="p-4">
            <FileList />
          </div>
        </div>
        
        {/* Main content area */}
        <div class="flex-1 p-4 overflow-y-auto">
          <ContentViewer />
        </div>
        
        {/* Right sidebar - Knowledge graph */}
        <div class="w-96 bg-gray-50 border-l border-gray-200">
          <div class="h-full p-4">
            <KnowledgeGraph />
          </div>
        </div>
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: 'Casys RPG - Espace Auteur',
  meta: [
    {
      name: 'description',
      content: 'Interface de gestion des sections pour les auteurs',
    },
  ],
};
