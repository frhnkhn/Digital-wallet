/**
 * security.c - Security & Encryption Module for Smart Digital Wallet
 * Language: C
 * Features: Pure-C SHA-256, random salt generation, password/PIN hashing
 * No external dependencies required.
 */

#include "security.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ================================================================
 *  Pure-C SHA-256 Implementation
 *  Based on the FIPS 180-4 specification
 * ================================================================ */

/* SHA-256 constants: first 32 bits of cube roots of first 64 primes */
static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

#define ROTR32(x,n) (((x) >> (n)) | ((x) << (32-(n))))
#define CH(x,y,z)   (((x)&(y))^(~(x)&(z)))
#define MAJ(x,y,z)  (((x)&(y))^((x)&(z))^((y)&(z)))
#define EP0(x)      (ROTR32(x,2)^ROTR32(x,13)^ROTR32(x,22))
#define EP1(x)      (ROTR32(x,6)^ROTR32(x,11)^ROTR32(x,25))
#define SIG0(x)     (ROTR32(x,7)^ROTR32(x,18)^((x)>>3))
#define SIG1(x)     (ROTR32(x,17)^ROTR32(x,19)^((x)>>10))

void sha256_init(SHA256_CTX_CUSTOM *ctx) {
    ctx->count = 0;
    /* Initial hash values: first 32 bits of square roots of first 8 primes */
    ctx->state[0] = 0x6a09e667;
    ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372;
    ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f;
    ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab;
    ctx->state[7] = 0x5be0cd19;
}

static void sha256_transform(SHA256_CTX_CUSTOM *ctx, const uint8_t data[64]) {
    uint32_t a, b, c, d, e, f, g, h, t1, t2, m[64];
    int i;

    for (i = 0; i < 16; i++) {
        m[i]  = ((uint32_t)data[i*4    ]) << 24;
        m[i] |= ((uint32_t)data[i*4 + 1]) << 16;
        m[i] |= ((uint32_t)data[i*4 + 2]) << 8;
        m[i] |= ((uint32_t)data[i*4 + 3]);
    }
    for (; i < 64; i++)
        m[i] = SIG1(m[i-2]) + m[i-7] + SIG0(m[i-15]) + m[i-16];

    a = ctx->state[0]; b = ctx->state[1];
    c = ctx->state[2]; d = ctx->state[3];
    e = ctx->state[4]; f = ctx->state[5];
    g = ctx->state[6]; h = ctx->state[7];

    for (i = 0; i < 64; i++) {
        t1 = h + EP1(e) + CH(e,f,g) + K[i] + m[i];
        t2 = EP0(a) + MAJ(a,b,c);
        h=g; g=f; f=e; e=d+t1;
        d=c; c=b; b=a; a=t1+t2;
    }

    ctx->state[0]+=a; ctx->state[1]+=b; ctx->state[2]+=c; ctx->state[3]+=d;
    ctx->state[4]+=e; ctx->state[5]+=f; ctx->state[6]+=g; ctx->state[7]+=h;
}

void sha256_update(SHA256_CTX_CUSTOM *ctx, const uint8_t *data, size_t len) {
    size_t i;
    for (i = 0; i < len; i++) {
        ctx->buffer[ctx->count % 64] = data[i];
        ctx->count++;
        if ((ctx->count % 64) == 0)
            sha256_transform(ctx, ctx->buffer);
    }
}

void sha256_final(SHA256_CTX_CUSTOM *ctx, uint8_t digest[SHA256_DIGEST]) {
    uint64_t bit_len = ctx->count * 8;
    uint32_t i = (uint32_t)(ctx->count % 64);

    ctx->buffer[i++] = 0x80;
    if (i > 56) {
        while (i < 64) ctx->buffer[i++] = 0x00;
        sha256_transform(ctx, ctx->buffer);
        i = 0;
    }
    while (i < 56) ctx->buffer[i++] = 0x00;

    /* Append length in bits (big-endian 64-bit) */
    for (int j = 7; j >= 0; j--) {
        ctx->buffer[56 + (7-j)] = (uint8_t)(bit_len >> (j*8));
    }
    sha256_transform(ctx, ctx->buffer);

    for (i = 0; i < 8; i++) {
        digest[i*4    ] = (ctx->state[i] >> 24) & 0xff;
        digest[i*4 + 1] = (ctx->state[i] >> 16) & 0xff;
        digest[i*4 + 2] = (ctx->state[i] >>  8) & 0xff;
        digest[i*4 + 3] = (ctx->state[i]       ) & 0xff;
    }
}

void sha256_hex(const uint8_t *data, size_t len, char out[HASH_LENGTH]) {
    SHA256_CTX_CUSTOM ctx;
    uint8_t digest[SHA256_DIGEST];
    sha256_init(&ctx);
    sha256_update(&ctx, data, len);
    sha256_final(&ctx, digest);
    for (int i = 0; i < SHA256_DIGEST; i++)
        snprintf(out + i*2, 3, "%02x", digest[i]);
    out[64] = '\0';
}

/* ================================================================
 *  Public Security API
 * ================================================================ */

/**
 * generate_salt - Creates a 32-char random hex salt.
 * Uses simple LCG seeded by time + clock for portability.
 */
void generate_salt(char out_salt[SALT_LENGTH + 1]) {
    static int seeded = 0;
    if (!seeded) {
        srand((unsigned int)(time(NULL) ^ (uintptr_t)out_salt));
        seeded = 1;
    }
    for (int i = 0; i < SALT_LENGTH; i++) {
        int r = rand() % 16;
        out_salt[i] = (r < 10) ? ('0' + r) : ('a' + r - 10);
    }
    out_salt[SALT_LENGTH] = '\0';
}

/**
 * hash_password - Concatenates password+salt then SHA-256 hashes it.
 */
void hash_password(const char *password, const char *salt, char out_hash[HASH_LENGTH]) {
    /* Build input: password + salt */
    size_t pw_len   = strlen(password);
    size_t salt_len = strlen(salt);
    size_t total    = pw_len + salt_len;
    uint8_t *buf    = (uint8_t *)malloc(total);
    if (!buf) { out_hash[0] = '\0'; return; }
    memcpy(buf, password, pw_len);
    memcpy(buf + pw_len, salt, salt_len);
    sha256_hex(buf, total, out_hash);
    free(buf);
}

/**
 * hash_pin - Same as hash_password but semantically for PINs.
 */
void hash_pin(const char *pin, const char *salt, char out_hash[HASH_LENGTH]) {
    hash_password(pin, salt, out_hash);
}

/**
 * verify_password - Returns 1 if hash matches, 0 otherwise.
 */
int verify_password(const char *input, const char *salt, const char *stored_hash) {
    char computed[HASH_LENGTH];
    hash_password(input, salt, computed);
    return (strncmp(computed, stored_hash, HASH_LENGTH) == 0) ? 1 : 0;
}

/**
 * verify_pin - Returns 1 if PIN hash matches, 0 otherwise.
 */
int verify_pin(const char *input_pin, const char *salt, const char *stored_hash) {
    return verify_password(input_pin, salt, stored_hash);
}

/**
 * generate_wallet_id - Creates a 16-char unique hex wallet ID.
 */
void generate_wallet_id(char out[17]) {
    static int seeded = 0;
    if (!seeded) {
        srand((unsigned int)(time(NULL)));
        seeded = 1;
    }
    /* Use time + random for uniqueness */
    uint64_t ts  = (uint64_t)time(NULL);
    uint64_t rnd = ((uint64_t)rand() << 32) | (uint64_t)rand();
    uint64_t val = ts ^ rnd;
    snprintf(out, 17, "%016llx", (unsigned long long)val);
    out[16] = '\0';
}
