import React, { useState, useEffect } from 'react';
import NewsCard from './NewsCard';
import { RefreshCw } from 'lucide-react';
import { getNewsFeed, getUrgentNews } from '../../services/news-api';

export default function NewsFeed() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Dynamic filters based on actual article categories
  const getAvailableFilters = () => {
    const baseFilters = [
      { label: 'All', value: 'all' },
      { label: 'Urgent', value: 'urgent' },
      { label: 'High Relevance', value: 'relevant' }
    ];

    // Get unique categories from articles
    const categories = [...new Set(articles.map(article => article.category))].sort();
    
    // Add dynamic category filters
    const categoryFilters = categories.map(category => ({
      label: category,
      value: category.toLowerCase()
    }));

    return [...baseFilters, ...categoryFilters];
  };

  const filters = getAvailableFilters();

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getNewsFeed();
      setArticles(data);
    } catch (error) {
      console.error('Error loading articles:', error);
      setError('Failed to load news.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const data = await getNewsFeed();
      setArticles(data);
    } catch {
      setError('Refresh failed.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleFilterChange = async (value) => {
    setFilter(value);
    if (value === 'urgent') {
      setLoading(true);
      try {
        const data = await getUrgentNews();
        setArticles(data);
      } catch {
        setError('Failed to load urgent news.');
      } finally {
        setLoading(false);
      }
    } else {
      await loadArticles();
    }
  };

  // Improved filtering logic to handle dynamic categories
  const filtered = articles.filter((article) => {
    if (filter === 'all') return true;
    if (filter === 'urgent') return article.urgency === 'high';
    if (filter === 'relevant') return article.relevanceScore >= 80;
    
    // Direct category matching (case-insensitive)
    const articleCategory = (article.category || '').toLowerCase().trim();
    const filterValue = filter.toLowerCase();
    
    return articleCategory === filterValue;
  });

  // Group articles for Perplexity-style layout (1 hero + 3 compact)
  const groupedArticles = [];
  for (let i = 0; i < filtered.length; i += 4) {
    const group = {
      hero: filtered[i],
      compact: filtered.slice(i + 1, i + 4)
    };
    groupedArticles.push(group);
  }

  return (
    <div className="h-screen bg-[#111111] text-[#fefce8] flex flex-col font-sans">
      {/* Filters */}
      <div className="w-full px-6 pt-6 pb-3">
        <div className="flex items-center gap-2 max-w-4xl mx-auto flex-wrap">
          {filters.map(f => (
            <button
              key={f.value}
              onClick={() => handleFilterChange(f.value)}
              className={`px-3 py-1.5 text-sm rounded-full border transition-all font-medium tracking-tight
                ${
                  filter === f.value
                    ? 'bg-[#facc15] text-black border-[#facc15]'
                    : 'bg-[#2d2d2d] border-[#3a3a3a] text-[#d4d4d4] hover:bg-[#3c3c3c]'
                }
              `}
            >
              {f.label}
            </button>
          ))}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="ml-auto px-3 py-1.5 flex items-center gap-1 text-sm bg-[#2d2d2d] text-[#d4d4d4] border border-[#3a3a3a] rounded-full hover:bg-[#3c3c3c] transition"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-[#a3a3a3]' : 'text-[#facc15]'}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Feed */}
      <div className="flex-1 overflow-y-auto thin-scrollbar">
        <div className="max-w-4xl mx-auto px-6 py-6">
          {loading ? (
            <div className="text-center text-[#a3a3a3] py-20">Loading your curated headlines...</div>
          ) : error ? (
            <div className="text-center text-red-300 bg-red-900/10 border border-red-600/30 rounded-lg p-4">
              {error}
            </div>
          ) : filtered.length > 0 ? (
            <div className="space-y-8">
              {groupedArticles.map((group, groupIndex) => (
                <div key={groupIndex} className="space-y-6">
                  {/* Hero Article */}
                  {group.hero && (
                    <NewsCard article={group.hero} layout="hero" />
                  )}
                  
                  {/* Three Compact Articles */}
                  {group.compact.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {group.compact.map((article) => (
                        <NewsCard key={article.id} article={article} layout="compact" />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-[#888] py-20">
              No news here. Try switching filters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}