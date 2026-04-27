/**
 * Strip <private>...</private> tags from text
 *
 * Users can wrap sensitive data in <private> tags to prevent it from being stored.
 * This function removes those tags and their content, replacing with [REDACTED].
 */
export function stripPrivateTags(text: string | null | undefined): string | null {
  if (!text) return text || null;

  // Remove <private> content but preserve structure
  return text.replace(/<private>[\s\S]*?<\/private>/g, '[REDACTED]');
}

/**
 * Strip <claude-mem-context>...</claude-mem-context> tags
 *
 * This prevents the plugin from re-ingesting its own injected context,
 * which would create an infinite loop.
 */
export function stripContextTags(text: string | null | undefined): string | null {
  if (!text) return text || null;

  return text.replace(/<claude-mem-context>[\s\S]*?<\/claude-mem-context>/g, '');
}

/**
 * Strip all memory-related tags
 */
export function stripAllMemoryTags(text: string | null | undefined): string | null {
  if (!text) return text || null;

  let cleaned = text;
  cleaned = stripPrivateTags(cleaned) || '';
  cleaned = stripContextTags(cleaned) || '';
  return cleaned;
}
