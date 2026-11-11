/**
 * Safe Word — client-side only, no network, offline capable.
 *
 * Generates a random shared phrase + a challenge question the user and
 * their trusted contact agree on in advance. Callers paste this in a
 * suspicious call to verify identity.
 */

const ADJECTIVES = [
  "नीला", "हिरवा", "पिवळा", "लाल", "काळा",
  "blue", "green", "yellow", "red", "silver",
  "नीला", "हरा", "पीला", "लाल", "काला",
];

const NOUNS = [
  "हत्ती", "वाघ", "कमळ", "आंबा", "पाऊस",
  "elephant", "tiger", "lotus", "mango", "monsoon",
  "हाथी", "बाघ", "कमल", "आम", "बारिश",
];

const CHALLENGES: Record<string, string[]> = {
  mr: [
    "आपल्या पहिल्या पाळीव प्राण्याचे नाव काय होते?",
    "लहानपणी आपले आवडते गाणे कोणते होते?",
    "आपल्या शाळेतील मित्राचे नाव सांगा.",
    "आपल्या आईचे माहेरचे नाव काय?",
    "आपण पहिल्यांदा कोणत्या शहरात राहिलात?",
  ],
  hi: [
    "आपके पहले पालतू जानवर का नाम क्या था?",
    "बचपन में आपका पसंदीदा गाना कौन सा था?",
    "अपने स्कूल के दोस्त का नाम बताइए।",
    "आपकी माँ का मायके का नाम क्या है?",
    "आप पहली बार किस शहर में रहे थे?",
  ],
  en: [
    "What was your first pet's name?",
    "What was your favourite childhood song?",
    "Name a close friend from school.",
    "What is your mother's maiden name initial?",
    "What was the first city you lived in?",
  ],
};

export interface SafeWordResult {
  phrase: string;
  challenge: string;
  shareText: string;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function generateSafeWord(lang: "mr" | "hi" | "en"): SafeWordResult {
  const phrase = `${pick(ADJECTIVES)} ${pick(NOUNS)}`.trim();
  const challenge = pick(CHALLENGES[lang]);
  const shareText = `Safe word: ${phrase}\nChallenge: ${challenge}`;
  return { phrase, challenge, shareText };
}

