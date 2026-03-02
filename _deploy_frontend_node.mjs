// Node.js frontend deploy script — uploads dist/ to S3 and invalidates CloudFront
import { S3Client, ListObjectsV2Command, DeleteObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { CloudFrontClient, ListDistributionsCommand, CreateInvalidationCommand } from '@aws-sdk/client-cloudfront';
import { readFileSync, readdirSync, statSync } from 'fs';
import { join, relative, extname } from 'path';

const BUCKET = 'smart-rural-ai-frontend-948809294205';
const REGION = 'ap-south-1';
const DIST_DIR = join(process.cwd(), 'frontend', 'dist');

const s3 = new S3Client({ region: REGION });
const cf = new CloudFrontClient({ region: 'us-east-1' });

const MIME_MAP = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.webp': 'image/webp',
};

function getAllFiles(dir) {
    const files = [];
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = join(dir, entry.name);
        if (entry.isDirectory()) files.push(...getAllFiles(full));
        else files.push(full);
    }
    return files;
}

async function main() {
    // 1. Clean existing frontend files from bucket
    console.log('=== Cleaning bucket ===');
    let deleted = 0;
    let token;
    do {
        const resp = await s3.send(new ListObjectsV2Command({
            Bucket: BUCKET,
            ContinuationToken: token
        }));
        token = resp.NextContinuationToken;
        for (const obj of (resp.Contents || [])) {
            if (obj.Key.startsWith('audio/') || obj.Key.startsWith('knowledge_base/') || obj.Key.startsWith('agentcore-code/')) continue;
            await s3.send(new DeleteObjectCommand({ Bucket: BUCKET, Key: obj.Key }));
            console.log(`  Deleted: ${obj.Key}`);
            deleted++;
        }
    } while (token);
    console.log(`  Deleted ${deleted} objects\n`);

    // 2. Upload dist/ files
    console.log('=== Uploading fresh build ===');
    const files = getAllFiles(DIST_DIR);
    let uploaded = 0;
    for (const filepath of files) {
        const key = relative(DIST_DIR, filepath).replace(/\\/g, '/');
        const ext = extname(filepath).toLowerCase();
        const contentType = MIME_MAP[ext] || 'application/octet-stream';
        const cacheControl = key.includes('assets/') ? 'max-age=31536000' : 'no-cache, no-store, must-revalidate';
        const body = readFileSync(filepath);

        await s3.send(new PutObjectCommand({
            Bucket: BUCKET,
            Key: key,
            Body: body,
            ContentType: contentType,
            CacheControl: cacheControl,
        }));
        console.log(`  ${key.padEnd(50)} ${body.length.toString().padStart(8)} bytes  (${contentType})`);
        uploaded++;
    }
    console.log(`\n  Uploaded ${uploaded} files`);

    // 3. Find CloudFront distribution and invalidate
    console.log('\n=== CloudFront invalidation ===');
    const dists = await cf.send(new ListDistributionsCommand({}));
    for (const d of (dists.DistributionList?.Items || [])) {
        const origins = d.Origins.Items.map(o => o.DomainName);
        if (origins.some(o => o.includes('smart-rural-ai-frontend'))) {
            console.log(`  Distribution: ${d.Id} (${d.Status})`);
            console.log(`  URL: https://${d.DomainName}`);
            if (d.Status === 'Deployed') {
                const inv = await cf.send(new CreateInvalidationCommand({
                    DistributionId: d.Id,
                    InvalidationBatch: {
                        Paths: { Quantity: 1, Items: ['/*'] },
                        CallerReference: String(Date.now()),
                    }
                }));
                console.log(`  Invalidation created: ${inv.Invalidation.Id}`);
            }
        }
    }
    console.log('\n=== Done! Changes will be live in ~60-90 seconds ===');
}

main().catch(err => { console.error(err); process.exit(1); });
