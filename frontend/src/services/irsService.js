/**
 * IRS Service
 * Handles loading and validating Insight Rendering Schema (IRS) configurations.
 */

export const irsService = {
  /**
   * Loads a schema from a local public asset or an external URL.
   * @param {string} fileName - The name of the JSON file (expected in /public)
   */
  async loadSchema(fileName = 'insight_schema.json') {
    try {
      // In a real dev environment, this would fetch from the public folder or an API
      const response = await fetch(`/${fileName}`);
      if (!response.ok) {
        throw new Error(`Failed to load IRS: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("IRS Loading Error:", error);
      throw error;
    }
  },

  /**
   * Helper to parse a JSON string into an IRS object with basic validation.
   * @param {string} jsonString 
   */
  parseSchema(jsonString) {
    try {
      const parsed = JSON.parse(jsonString);
      if (!parsed.title || !parsed.visuals) {
        throw new Error("Invalid IRS: Missing mandatory fields (title/visuals)");
      }
      return parsed;
    } catch (error) {
      throw new Error(`JSON Schema Error: ${error.message}`);
    }
  }
};
