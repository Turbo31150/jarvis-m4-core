[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Pourquoi un PC Linux se fige-t-il et redémarre après quelques minutes, sur cette configuration précise : Ubuntu, noyau 6.8.0-136-generic, CPU AMD Ryzen 5000 série Vermeer (famille 19h, modèle 21h, stepping 2, socket AM4, carte mère MSI MS-7C56 / B550), 46 Gio de RAM non-ECC (deux kits mixtes, spec 3200 MT/s poussés à 3666), 4 GPU NVIDIA avec pilote propriétaire DKMS, zram + swap NVMe, Docker Swarm et de nombreux services systemd.

Deux hypothèses à instruire et à départager :

(A) HYPOTHÈSE LOGICIELLE — use-after-free du noyau dans le pid IDR. Symptômes observés : des services systemd déclarés Type=simple + Restart=always sur des scripts one-shot qui sortent en exit 0, provoquant 50+ redémarrages en 10 minutes ; puis des « general protection fault, probably for non-canonical address », « BUG: unable to handle page fault », « Oops [#1..#3] PREEMPT SMP NOPTI », « TASK stack guard page was hit », frappant simultanément plusieurs processus userspace sans rapport (python3, llama-server) ; ensuite toute itération de /proc (ps, pgrep, top) ajoute un Oops via next_tgid / proc_pid_readdir / getdents64, le load monte à plusieurs centaines et la machine gèle.
Questions : ce bug est-il documenté en amont (LKML, bugzilla kernel.org, Launchpad Ubuntu, CVE) ? Quelles versions de Linux sont affectées et à partir de quel commit / quelle version stable est-il corri

[assistant] Local bit-decode confirms HWID=0x02e, McaType=0x0001. Now verifying the table mapping against primary sources.

[assistant] Verification complete. Local arithmetic and two primary sources (rasdaemon master + kernel/LKML) agree.