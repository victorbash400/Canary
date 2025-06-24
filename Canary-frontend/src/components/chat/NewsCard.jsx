import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle,
  Clock,
  ChevronDown,
  ExternalLink,
  Brain,
  Link,
} from 'lucide-react';

const DEFAULT_IMAGE = 'https://via.placeholder.com/800x400/2d2d2d/facc15?text=No+Image';

const CardHeader = ({ imageUrl, title, category, publishedAt, urgency }) => {
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return '...';
    const diff = Date.now() - new Date(timestamp).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <motion.div
      initial={{ opacity: 0.85, scale: 1 }}
      animate={{ opacity: 1, scale: 1.015 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="relative overflow-hidden rounded-t-xl"
    >
      <div className="w-full aspect-video bg-gray-800">
        <img
          src={imageUrl || DEFAULT_IMAGE}
          alt={title}
          className="w-full h-full object-cover transition-transform duration-500 hover:scale-[1.025]"
        />
      </div>
      <div className="absolute bottom-0 left-0 w-full h-2/3 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
      <div className="absolute bottom-0 left-0 p-4 w-full">
        <div className="flex items-center gap-3 text-xs text-gray-300 mb-2">
          {urgency === 'high' && (
            <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
          )}
          <span className="bg-yellow-400/10 backdrop-blur-sm text-yellow-300 px-2 py-0.5 rounded-full uppercase tracking-wide text-[10px] font-semibold hover:bg-yellow-400/20 transition-colors">
            {category}
          </span>
          <span className="flex items-center gap-1.5 backdrop-blur-sm bg-black/30 px-2 py-0.5 rounded-full">
            <Clock className="w-3 h-3" />
            {formatTimeAgo(publishedAt)}
          </span>
        </div>
        <h3 className="text-lg font-bold text-white leading-snug tracking-tight">
          {title}
        </h3>
      </div>
    </motion.div>
  );
};

const ExpandedContent = ({ gemini_analysis, citations, expanded }) => {
  const [activeTab, setActiveTab] = useState('ai');

  const TabButton = ({ label, tab, icon: Icon }) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${
        activeTab === tab
          ? 'bg-yellow-300/20 text-yellow-300 shadow-sm shadow-yellow-300/10' // Increased opacity for selected tab
          : 'text-gray-300 hover:bg-white/10 hover:text-white' // Slightly stronger hover
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  );

  return (
    <motion.div
      initial={false}
      animate={{
        height: expanded ? 'auto' : 0,
        opacity: expanded ? 1 : 0,
      }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="overflow-hidden"
    >
      <div className="px-4 pb-4 pt-1">
        <div className="flex items-center gap-2 pb-3 mb-3">
          <TabButton label="AI Insights" tab="ai" icon={Brain} />
          <TabButton label="Sources" tab="sources" icon={Link} />
        </div>

        {activeTab === 'ai' && (
          !gemini_analysis ? (
            <p className="text-sm text-gray-500">No AI analysis available.</p>
          ) : (
            <div className="space-y-4 text-sm text-gray-300">
              {gemini_analysis.key_points?.length > 0 && (
                <ul className="space-y-1.5 list-inside">
                  {gemini_analysis.key_points.map((pt, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-yellow-400 mt-1">&#8227;</span>
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex flex-wrap items-center gap-2 pt-2">
                {gemini_analysis.sentiment && (
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      gemini_analysis.sentiment === 'positive'
                        ? 'bg-green-900/50 text-green-300'
                        : gemini_analysis.sentiment === 'negative'
                        ? 'bg-red-900/50 text-red-300'
                        : 'bg-gray-700 text-gray-300'
                    }`}
                  >
                    Sentiment: {gemini_analysis.sentiment}
                  </span>
                )}
                {gemini_analysis.tags?.map((tag, idx) => (
                  <span
                    key={idx}
                    className="bg-gray-700/50 text-gray-300 text-xs px-2 py-1 rounded-full"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )
        )}

        {activeTab === 'sources' && (
          <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
            {citations?.length ? (
              citations.map((link, idx) => {
                const domain = new URL(link).hostname.replace('www.', '');
                return (
                  <a
                    key={idx}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 text-sm text-blue-400 hover:text-blue-300 bg-white/10 hover:bg-white/20 p-2 rounded-xl transition-all duration-200 group" // Slightly increased bg opacity
                  >
                    <Link className="w-4 h-4 flex-shrink-0 text-gray-400" /> {/* Changed icon color slightly */}
                    <span className="truncate group-hover:underline">
                      {domain}
                    </span>
                  </a>
                );
              })
            ) : (
              <p className="text-sm text-gray-500">No citations available.</p>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default function NewsCardV2({ article }) {
  const [expanded, setExpanded] = useState(false);

  const {
    title,
    summary,
    category,
    publishedAt,
    url,
    imageUrl,
    urgency,
    citations,
    gemini_analysis,
  } = article;

  return (
    <motion.div
      whileHover={{ scale: 1.003 }}
      // Adjusted background, removed border, added backdrop-filter for glassmorphism
      className="bg-white/5 rounded-2xl shadow-lg shadow-black/30 overflow-hidden flex flex-col transition-all backdrop-blur-xl border border-white/10"
    >
      <div className="cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <CardHeader
          imageUrl={imageUrl}
          title={title}
          category={category}
          publishedAt={publishedAt}
          urgency={urgency}
        />
        <div className="p-4 pt-3">
          <p className="text-sm text-gray-300 line-clamp-3 leading-relaxed tracking-tight"> {/* Slightly lightened text */}
            {summary}
          </p>
        </div>
      </div>

      <ExpandedContent
        gemini_analysis={gemini_analysis}
        citations={citations}
        expanded={expanded}
      />

      {/* Removed border-t and adjusted padding for a cleaner look */}
      <div className="flex justify-between items-center text-sm text-gray-400 p-4 pt-2">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 text-yellow-300 hover:text-yellow-200 transition-colors px-2 py-1"
        >
          {expanded ? 'Show Less' : 'Show More'}
          <motion.div
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            <ChevronDown className="w-4 h-4" />
          </motion.div>
        </button>

        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          // Adjusted background and border for a more subtle Google-like button
          className="flex items-center gap-1.5 backdrop-blur-md bg-white/10 hover:bg-white/20 text-yellow-300 font-medium px-3 py-1.5 rounded-lg transition-all duration-200 border border-white/20 hover:border-white/30"
        >
          Read Full Story <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </motion.div>
  );
}