# Isolation des Processus via Namespaces de Mémoire (Memory Namespace Isolation)

*Domaine : Linux Kernel*

# Isolation des Processus via les Namespaces de Mémoire sur Linux

## Contexte
Sur le noyau Linux moderne (généralement depuis la version 3.8), l'isolation mémoire n'est plus une fonctionnalité optionnelle mais intégrée par défaut grâce aux **Namespaces**. Contrairement aux conteneurs Docker ou LXC qui reposent souvent sur `cgroups` pour limiter les ressources, les namespaces offrent une isolation logique de l'espace d'adressage.

Le mécanisme clé ici est le namespace `/proc/<pid>/maps`. Par défaut, tous les processus partagent la même vue de l'espace physique et virtuel. L'activation du flag `private_mem` (via `clone_flags`) permet à un nouveau namespace de percevoir sa propre copie privée des pages mémoire partagées par le parent. C'est la fondation technique pour créer des environnements sandboxés sans surcharge matérielle significative.

## Points Clés
*   **Copie-on-Write (CoW) :** L'isolation repose sur la politique CoW du noyau. Les pages de mémoire partagées sont copiées physiquement uniquement lorsqu'un processus tente d'écrire dessus. Avant cela, l'espace virtuel semble identique pour tous les membres du namespace.
*   **Séparation Virtuelle vs Physique :** Un namespace permet de mapper des adresses virtuelles différentes sur le même contenu physique (ou inversement), rendant impossible la lecture directe de la mémoire d'un autre processus sans privilèges, même si l'adresse virtuelle est connue.
*   **Gestion du `mmap` :** Les appels système comme `mmap()` ou `brk()` créent des régions privées par défaut dans un nouveau namespace. Les régions partagées (comme les bibliothèques `.so`) nécessitent une configuration explicite pour être isolées si le but est la confidentialité stricte.
*   **Intégration avec cgroups :** Pour une isolation complète, les namespaces de mémoire doivent souvent être combinés avec `cgroups v2` pour limiter l'allocation physique réelle (RAM), évitant ainsi qu'un processus isolé ne consume toute la RAM du hôte via des fuites ou des attaques par débordement.

## Exemple Concret : Création d'un Namespace Mémoire
Voici un script Python utilisant `subprocess` pour illustrer la création d'un namespace mémoire privé (`CLONE_NEWUSER | CLONE_NEWPID | CLONE_PRIVATE_MEM`) :

```python
import subprocess
import os

# Flags nécessaires : Nouveau User, Nouveau PID, et Isolation Mémoire Privée
flags = 0x10000000 | 0x20000000 | 0x80000000 # CLONE_NEWUSER | CLONE_NEWPID | CLONE
