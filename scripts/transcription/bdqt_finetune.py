#!/usr/bin/env python3
"""Étape 3 : fine-tuning Whisper sur la voix de l'utilisatrice (LoRA/PEFT).

⚠️ NÉCESSITE UN VRAI GPU (≥8 Go pour small, ≥16 Go pour large-v3). Le M4 (4 Go)
ne suffit PAS. Lancer sur cluster M1/M2 ou GPU cloud. Dataset déjà prêt :
  ~/jarvis/voice_dataset/train.jsonl + eval.jsonl  (audio WAV 16kHz + text)

Installe d'abord :
  pip install torch transformers datasets peft accelerate evaluate jiwer soundfile

Usage :
  python bdqt_finetune.py --model openai/whisper-small        # rentre dans ~8 Go
  python bdqt_finetune.py --model openai/whisper-large-v3 --base_only_eval   # éval baseline

Sortie : ~/jarvis/voice_dataset/whisper-lora-pamerys/ (adaptateur LoRA)
Pour servir ensuite : fusionner l'adaptateur et convertir en faster-whisper (ct2),
puis pointer whisper-server dessus via JARVIS_WHISPER_MODEL.
"""

import argparse
import json
import os

DS = os.path.expanduser("~/jarvis/voice_dataset")


def load_rows(name):
    return [json.loads(line) for line in open(f"{DS}/{name}.jsonl", encoding="utf-8")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openai/whisper-small")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", default=f"{DS}/whisper-lora-pamerys")
    ap.add_argument("--base_only_eval", action="store_true")
    args = ap.parse_args()

    import torch
    from datasets import Dataset, Audio
    from transformers import (
        WhisperProcessor,
        WhisperForConditionalGeneration,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        DataCollatorForSeq2Seq,
    )
    from peft import LoraConfig, get_peft_model

    proc = WhisperProcessor.from_pretrained(
        args.model, language="fr", task="transcribe"
    )

    def to_ds(rows):
        d = Dataset.from_list(
            [{"audio": f"{DS}/{r['audio']}", "text": r["text"]} for r in rows]
        )
        return d.cast_column("audio", Audio(sampling_rate=16000))

    train_ds, eval_ds = to_ds(load_rows("train")), to_ds(load_rows("eval"))

    def prep(b):
        a = b["audio"]
        b["input_features"] = proc(a["array"], sampling_rate=16000).input_features[0]
        b["labels"] = proc(text=b["text"]).input_ids
        return b

    train_ds = train_ds.map(prep, remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(prep, remove_columns=eval_ds.column_names)

    model = WhisperForConditionalGeneration.from_pretrained(args.model)
    if not args.base_only_eval:
        lora = LoraConfig(
            r=32,
            lora_alpha=64,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
        )
        model = get_peft_model(model, lora)
        model.print_trainable_parameters()

    collator = DataCollatorForSeq2Seq(proc.tokenizer, model=model)
    targs = Seq2SeqTrainingArguments(
        output_dir=args.out,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        fp16=torch.cuda.is_available(),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
        predict_with_generate=True,
        report_to="none",
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=collator,
        tokenizer=proc.feature_extractor,
    )
    if args.base_only_eval:
        print(trainer.evaluate())
        return
    trainer.train()
    model.save_pretrained(args.out)
    proc.save_pretrained(args.out)
    print(f"[finetune] adaptateur LoRA sauvé -> {args.out}")


if __name__ == "__main__":
    main()
