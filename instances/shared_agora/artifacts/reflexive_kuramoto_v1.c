#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>

/* Fast xorshift64* PRNG; returns 64-bit unsigned integer. */
static uint64_t rng_state[1];

uint64_t xorshift64s(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    *state = x;
    return x;
}

/* Uniform double in (0,1). */
double rng_uniform(uint64_t *s) {
    uint64_t r = xorshift64s(s);
    return (r >> 11) * (1.0 / (1ULL << 53)); } /* Box-Muller: returns standard normal variates in pairs. */
void rng_normal_pair(uint64_t *s, double *n1, double *n2) {
    double u1, u2, radius, theta;
    u1 = rng_uniform(s);
    u2 = rng_uniform(s);
    radius = sqrt(-2.0 * log(u1));
    theta = 2.0 * M_PI * u2;
    *n1 = radius * cos(theta);
    *n2 = radius * sin(theta);
}

/* Run one trajectory. Returns time-averaged R over measurement window. */
double simulate_one(int N, double K0, double alpha, double sigma, double dt,
                    int n_trans, int n_meas, uint64_t *s) {
    double *theta = (double*)malloc(N * sizeof(double));
    int spare_ready = 0;
    double spare;

    for (int i = 0; i < N; i++) {
        theta[i] = 2.0 * M_PI * rng_uniform(s);
    }

    int nsteps = n_trans + n_meas;
    double R_acc = 0.0;

    for (int t = 0; t < nsteps; t++) {
        double csum = 0.0, ssum = 0.0;
        for (int i = 0; i < N; i++) {
            csum += cos(theta[i]);
            ssum += sin(theta[i]);
        }
        double R = sqrt(csum * csum + ssum * ssum) / N;
        double psi = atan2(ssum, csum);
        double K = (R > 0.0 ? K0 * pow(R, alpha) : 0.0);
        double noise_amp = sigma * sqrt(dt);

        /* Update phases in-place. Use the mean-field trick. */
        for (int i = 0; i < N; i++) {
            double n;
            if (spare_ready) {
                n = spare;
                spare_ready = 0;
            } else {
                rng_normal_pair(s, &n, &spare);
                spare_ready = 1;
            }
            theta[i] += K * R * sin(psi - theta[i]) * dt + noise_amp * n;
        }

        if (t >= n_trans) {
            R_acc += R;
        }
    }

    free(theta);
    return R_acc / n_meas;
}

int main(int argc, char **argv) {
    if (argc < 11) {
        fprintf(stderr, "Usage: %s N alpha sigma dt T_trans T_meas n_seeds seed_base K0_min K0_max n_K out_prefix\n", argv[0]);
        return 1;
    }
    int N = atoi(argv[1]);
    double alpha = atof(argv[2]);
    double sigma = atof(argv[3]);
    double dt = atof(argv[4]);
    double T_trans = atof(argv[5]);
    double T_meas = atof(argv[6]);
    int n_seeds = atoi(argv[7]);
    uint64_t seed_base = (uint64_t)atoll(argv[8]);
    double K0_min = atof(argv[9]);
    double K0_max = atof(argv[10]);
    int n_K = atoi(argv[11]);
    const char *out_prefix = argv[12];

    int n_trans = (int)(T_trans / dt);
    int n_meas = (int)(T_meas / dt);

    char datafile[1024];
    snprintf(datafile, sizeof(datafile), "%s_N%d.dat", out_prefix, N);
    FILE *fp = fopen(datafile, "w");
    if (!fp) { perror("fopen"); return 1; }
    fprintf(fp, "# K0 R_mean R_std\n");

    double *means = (double*)malloc(n_K * sizeof(double));
    double Kc = -1.0;
    for (int ik = 0; ik < n_K; ik++) {
        double K0 = K0_min + ik * (K0_max - K0_min) / (n_K - 1);
        double sum = 0.0, sum2 = 0.0;
        for (int s = 0; s < n_seeds; s++) {
            uint64_t state = seed_base + (uint64_t)ik * 1000000ULL + (uint64_t)s * 1000ULL + (uint64_t)N;
            double R = simulate_one(N, K0, alpha, sigma, dt, n_trans, n_meas, &state);
            sum += R;
            sum2 += R * R;
        }
        double mean = sum / n_seeds;
        double std = sqrt((sum2 / n_seeds) - mean * mean);
        means[ik] = mean;
        fprintf(fp, "%.6f %.6f %.6f\n", K0, mean, std);
        if (Kc < 0 && mean >= 0.5) Kc = K0;
    }
    fclose(fp);

    char jsonfile[1024];
    snprintf(jsonfile, sizeof(jsonfile), "%s_N%d.json", out_prefix, N);
    FILE *fj = fopen(jsonfile, "w");
    if (!fj) { perror("fopen json"); return 1; }
    fprintf(fj, "{\n");
    fprintf(fj, "  \"N\": %d,\n", N);
    fprintf(fj, "  \"alpha\": %.4f,\n", alpha);
    fprintf(fj, "  \"sigma\": %.6f,\n", sigma);
    fprintf(fj, "  \"dt\": %.4f,\n", dt);
    fprintf(fj, "  \"T_trans\": %.2f,\n", T_trans);
    fprintf(fj, "  \"T_meas\": %.2f,\n", T_meas);
    fprintf(fj, "  \"n_seeds\": %d,\n", n_seeds);
    fprintf(fj, "  \"seed_base\": %llu,\n", (unsigned long long)seed_base);
    fprintf(fj, "  \"K0_min\": %.6f,\n", K0_min);
    fprintf(fj, "  \"K0_max\": %.6f,\n", K0_max);
    fprintf(fj, "  \"n_K\": %d,\n", n_K);
    fprintf(fj, "  \"Kc_threshold\": %.4f,\n", 0.5);
    fprintf(fj, "  \"Kc\": %.6f,\n", Kc);
    fprintf(fj, "  \"K0\": [");
    for (int ik = 0; ik < n_K; ik++) {
        double K0 = K0_min + ik * (K0_max - K0_min) / (n_K - 1);
        fprintf(fj, "%.6f%s", K0, ik < n_K - 1 ? ", " : "");
    }
    fprintf(fj, "],\n  \"R_mean\": [");
    for (int ik = 0; ik < n_K; ik++) {
        fprintf(fj, "%.6f%s", means[ik], ik < n_K - 1 ? ", " : "");
    }
    fprintf(fj, "]\n}\n");
    fclose(fj);

    printf("N=%d Kc=%.6f\n", N, Kc);
    free(means);
    return 0;
}
