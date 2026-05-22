import SearchForm from '@/components/SearchForm';

export default function Home() {
  return (
    <div className="py-12">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Second Brain
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your personal knowledge management system. Search, discover, and explore
          your entire knowledge graph with semantic search and entity relationships.
        </p>
      </div>

      <div className="mb-12">
        <SearchForm />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
        <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Semantic Search
          </h3>
          <p className="text-blue-700">
            Find relevant information using natural language queries powered by
            embeddings and vector search.
          </p>
        </div>

        <div className="bg-green-50 p-6 rounded-lg border border-green-200">
          <h3 className="text-lg font-semibold text-green-900 mb-2">
            Entity Explorer
          </h3>
          <p className="text-green-700">
            Discover entities, their relationships, and all documents mentioning
            them in your knowledge base.
          </p>
        </div>

        <div className="bg-purple-50 p-6 rounded-lg border border-purple-200">
          <h3 className="text-lg font-semibold text-purple-900 mb-2">
            Graph Visualization
          </h3>
          <p className="text-purple-700">
            Visualize the knowledge graph to understand connections between
            entities and concepts.
          </p>
        </div>
      </div>
    </div>
  );
}
