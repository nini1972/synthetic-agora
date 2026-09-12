/*
High-performance C reference implementation for the reflexive-coupling
Kuramoto finite-size scaling sweep.

Compile:  gcc -O2 -march=native -std=gnu99 -lm -o kuramoto_scaling_kimi kuramoto_scaling_kimi.c
Run:      ./kuramoto_scaling_kimi N n_seeds Kmin Kmax dK dt trans T alpha sigma seed_base

Output JSON to stdout:
  {"N": ..., "K0s": [...], "R_mean": [[...seeds...], ...K...]}
*/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>

static inline double randn_pair(double *cache, int *has) {
    if (*has) { *has = 0; return *cache; }
    double u, v, r2;
    do {
        u = 2.0 * drand48() - 1.0;
        v = 2.0 * drand48() - 1.0;
        r2 = u*u + v*v;
    } while (r2 >= 1.0 || r2 == 0.0);
    double fac = sqrt(-2.0 * log(r2) / r2);
    *cache = v * fac;
    *has = 1;
    return u * fac;
}

int main(int argc, char **argv) {
    if (argc < 11) {
        fprintf(stderr, "Usage: %s N n_seeds Kmin Kmax dK dt trans T alpha sigma [seed_base]\n", argv[0]);
        return 1;
    }
    int N = atoi(argv[1]);
    int seeds = atoi(argv[2]);
    double Kmin = atof(argv[3]);
    double Kmax = atof(argv[4]);
    double dK = atof(argv[5]);
    double dt = atof(argv[6]);
    double trans = atof(argv[7]);
    double T = atof(argv[8]);
    double alpha = atof(argv[9]);
    double sigma = atof(argv[10]);
    long seed_base = (argc > 11) ? atol(argv[11]) : 12345L;

    int nK = (int)round((Kmax - Kmin) / dK) + 1;
    if (nK < 1) nK = 1;
    int n_total = (int)(T / dt);
    int n_trans = (int)(trans / dt);
    double noise_scale = sigma * sqrt(dt);
    double pow_exp = 1.0 + alpha;

    // Arrays: theta, cos_t, sin_t size N x seeds
    double *theta = (double*)malloc(N * seeds * sizeof(double));
    double *cos_t = (double*)malloc(N * seeds * sizeof(double));
    double *sin_t = (double*)malloc(N * seeds * sizeof(double));
    // R_mean[K][seed]
    double *R_mean = (double*)calloc((size_t)nK * seeds, sizeof(double));
    double *C = (double*)malloc(seeds * sizeof(double));
    double *S = (double*)malloc(seeds * sizeof(double));
    double *R = (double*)malloc(seeds * sizeof(double));
    double *factor = (double*)malloc(seeds * sizeof(double));

    if (!theta || !cos_t || !sin_t || !R_mean || !C || !S || !R || !factor) {
        fprintf(stderr, "Memory allocation failed\n");
        return 2;
    }

    srand48(seed_base + N);

    for (int ik = 0; ik < nK; ++ik) {
        double K0 = Kmin + ik * dK;
        // initialize phases uniformly
        for (int i = 0; i < N; ++i) {
            for (int s = 0; s < seeds; ++s) {
                theta[i*seeds + s] = 2.0 * M_PI * drand48();
            }
        }
        memset(R_mean + (size_t)ik * seeds, 0, seeds * sizeof(double));
        int count = 0;
        for (int step = 0; step < n_total; ++step) {
            // compute cos/sin and sum
            for (int s = 0; s < seeds; ++s) { C[s] = 0.0; S[s] = 0.0; }
            for (int i = 0; i < N; ++i) {
                for (int s = 0; s < seeds; ++s) {
                    double th = theta[i*seeds + s];
                    double c = cos(th);
                    double sth = sin(th);
                    cos_t[i*seeds + s] = c;
                    sin_t[i*seeds + s] = sth;
                    C[s] += c;
                    S[s] += sth;
                }
            }
            for (int s = 0; s < seeds; ++s) {
                double cs = C[s] / N;
                double ss = S[s] / N;
                R[s] = sqrt(cs*cs + ss*ss);
                double psi = atan2(ss, cs);
                double sf = sin(psi);
                double cf = cos(psi);
                factor[s] = K0 * pow(R[s], pow_exp);
                // update each oscillator
                int has = 0;
                double cache = 0.0;
                for (int i = 0; i < N; ++i) {
                    int idx = i*seeds + s;
                    double inter = factor[s] * (sf * cos_t[idx] - cf * sin_t[idx]);
                    double xi = randn_pair(&cache, &has);
                    theta[idx] += dt * inter + noise_scale * xi;
                }
            }
            if (step >= n_trans) {
                for (int s = 0; s < seeds; ++s) {
                    R_mean[(size_t)ik * seeds + s] += R[s];
                }
                ++count;
            }
        }
        if (count > 0) {
            for (int s = 0; s < seeds; ++s) {
                R_mean[(size_t)ik * seeds + s] /= count;
            }
        }
    }

    // Output JSON
    printf("{\"N\":%d, \"K0s\":[", N);
    for (int ik = 0; ik < nK; ++ik) {
        printf("%.4f%s", Kmin + ik*dK, (ik < nK-1) ? ", " : "");
    }
    printf("], \"R_mean\":[");
    for (int ik = 0; ik < nK; ++ik) {
        printf("[");
        for (int s = 0; s < seeds; ++s) {
            printf("%.6f%s", R_mean[(size_t)ik*seeds + s], (s < seeds-1) ? ", " : "");
        }
        printf("]%s", (ik < nK-1) ? ", " : "");
    }
    printf("]}\n");

    free(theta); free(cos_t); free(sin_t); free(R_mean);
    free(C); free(S); free(R); free(factor);
    return 0;
}
