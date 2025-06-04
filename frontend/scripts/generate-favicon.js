import * as Jimp from 'jimp';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function generateFavicon() {
  try {
    // Input logo path
    const inputPath = join(__dirname, '../public/images/logo.png');
    // Output favicon path
    const outputPath = join(__dirname, '../public/favicon.png');

    // Read the image
    const image = await Jimp.read(inputPath);
    
    // Resize to 32x32 (standard favicon size)
    image.resize(32, 32);
    
    // Save as PNG (most modern browsers support PNG favicons)
    await image.writeAsync(outputPath);

    console.log('Favicon generated successfully!');
  } catch (error) {
    console.error('Error generating favicon:', error);
  }
}

generateFavicon(); 