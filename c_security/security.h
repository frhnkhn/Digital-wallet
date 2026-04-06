/**
 * security.h - Security & Encryption Module for Smart Digital Wallet
 * Language: C
 * Purpose: PIN/password hashing, salt generation, verification
 */

#ifndef SECURITY_H
#define SECURITY_H

#include <stdint.h>
#include <stddef.h>

/* Output buffer sizes */
#define SALT_LENGTH     32   /* 16 bytes hex-encoded = 32 chars */
#define HASH_LENGTH     65   /* SHA-256 = 32 bytes = 64 hex chars + null */
#define SHA256_BLOCK    64
#define SHA256_DIGEST   32

/* ---- SHA-256 context (pure C, no OpenSSL needed) ---- */
typedef struct {
    uint32_t state[8];
    uint64_t count;
    uint8_t  buffer[64];
} SHA256_CTX_CUSTOM;

/* Low-level SHA-256 */
void sha256_init   (SHA256_CTX_CUSTOM *ctx);
void sha256_update (SHA256_CTX_CUSTOM *ctx, const uint8_t *data, size_t len);
void sha256_final  (SHA256_CTX_CUSTOM *ctx, uint8_t digest[SHA256_DIGEST]);
void sha256_hex    (const uint8_t *data, size_t len, char out[HASH_LENGTH]);

/* ---- Public Security API ---- */

/**
 * generate_salt - fills out_salt (SALT_LENGTH+1 bytes) with a
 *                 random hex string.
 */
void generate_salt(char out_salt[SALT_LENGTH + 1]);

/**
 * hash_password - SHA-256(password + salt), result written to out_hash.
 * out_hash must be at least HASH_LENGTH bytes.
 */
void hash_password(const char *password, const char *salt, char out_hash[HASH_LENGTH]);

/**
 * hash_pin - SHA-256(pin + salt), written to out_hash.
 */
void hash_pin(const char *pin, const char *salt, char out_hash[HASH_LENGTH]);

/**
 * verify_password - returns 1 if hash_password(input,salt)==stored_hash,
 *                   0 otherwise.
 */
int verify_password(const char *input, const char *salt, const char *stored_hash);

/**
 * verify_pin - same as verify_password but for PINs.
 */
int verify_pin(const char *input_pin, const char *salt, const char *stored_hash);

/**
 * generate_wallet_id - generates a unique wallet ID string (16 hex chars).
 * out must be at least 17 bytes.
 */
void generate_wallet_id(char out[17]);

#endif /* SECURITY_H */
