import { App, Modal, SearchComponent } from 'obsidian';

interface SearchResult {
  doc_id: string;
  title: string;
  excerpt: string;
  relevance_score: number;
  source_type: string;
}

export default class SearchModal extends Modal {
  apiUrl: string;
  results: SearchResult[] = [];

  constructor(app: App, apiUrl: string) {
    super(app);
    this.apiUrl = apiUrl;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();

    contentEl.createEl('h2', { text: 'Search Second Brain' });

    const searchContainer = contentEl.createEl('div', {
      cls: 'search-container',
    });

    const searchInput = searchContainer.createEl('input', {
      type: 'text',
      placeholder: 'Enter search query...',
    });

    searchInput.style.width = '100%';
    searchInput.style.padding = '8px';
    searchInput.style.marginBottom = '16px';
    searchInput.style.borderRadius = '4px';
    searchInput.style.border = '1px solid #ddd';

    const resultsContainer = contentEl.createEl('div', {
      cls: 'results-container',
    });

    const performSearch = async () => {
      const query = searchInput.value.trim();
      if (!query) return;

      resultsContainer.empty();
      resultsContainer.createEl('p', {
        text: 'Searching...',
        cls: 'search-status',
      });

      try {
        const response = await fetch(
          `${this.apiUrl}/search`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              top_k: 10,
              include_metadata: true,
            }),
          }
        );

        if (!response.ok) {
          throw new Error('Search failed');
        }

        const data = await response.json();
        this.results = data.results || [];
        this.displayResults(resultsContainer);
      } catch (error) {
        resultsContainer.empty();
        resultsContainer.createEl('p', {
          text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
          cls: 'search-error',
        });
      }
    };

    const searchButton = searchContainer.createEl('button', {
      text: 'Search',
      cls: 'mod-cta',
    });

    searchButton.style.marginBottom = '16px';
    searchButton.style.padding = '8px 16px';
    searchButton.style.cursor = 'pointer';

    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        performSearch();
      }
    });

    contentEl.appendChild(searchContainer);
    contentEl.appendChild(resultsContainer);
  }

  private displayResults(container: HTMLElement) {
    container.empty();

    if (this.results.length === 0) {
      container.createEl('p', { text: 'No results found.' });
      return;
    }

    container.createEl('h3', {
      text: `Found ${this.results.length} results`,
    });

    const resultsList = container.createEl('div', { cls: 'results-list' });

    this.results.forEach((result) => {
      const resultItem = resultsList.createEl('div', {
        cls: 'result-item',
      });

      resultItem.style.padding = '12px';
      resultItem.style.marginBottom = '12px';
      resultItem.style.border = '1px solid #ddd';
      resultItem.style.borderRadius = '4px';
      resultItem.style.cursor = 'pointer';
      resultItem.style.backgroundColor = '#f9f9f9';

      resultItem.createEl('h4', {
        text: result.title,
        cls: 'result-title',
      });

      resultItem.createEl('p', {
        text: result.excerpt,
        cls: 'result-excerpt',
      });

      const metadata = resultItem.createEl('div', {
        cls: 'result-metadata',
      });

      metadata.style.fontSize = '0.85em';
      metadata.style.color = '#666';
      metadata.style.marginTop = '8px';

      metadata.createEl('span', {
        text: `Type: ${result.source_type} | Relevance: ${(
          result.relevance_score * 100
        ).toFixed(0)}%`,
      });

      resultItem.addEventListener('click', () => {
        console.log('Clicked result:', result);
        this.close();
      });

      resultItem.addEventListener('mouseover', () => {
        resultItem.style.backgroundColor = '#f0f0f0';
        resultItem.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
      });

      resultItem.addEventListener('mouseout', () => {
        resultItem.style.backgroundColor = '#f9f9f9';
        resultItem.style.boxShadow = 'none';
      });
    });
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}
