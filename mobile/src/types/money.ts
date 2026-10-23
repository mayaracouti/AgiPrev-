// Monetary values cross the REST boundary as decimal strings, never JS arithmetic floats.
// Formatting, validation and calculations will follow the business contracts.
export type MoneyAmount = string;
