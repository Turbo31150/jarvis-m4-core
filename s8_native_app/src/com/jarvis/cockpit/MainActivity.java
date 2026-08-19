package com.jarvis.cockpit;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Vibrator;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;

public class MainActivity extends Activity {

    private static final String[] CANDIDATE_HOSTS = {
        "http://192.168.0.20:8799",      // M4 WiFi LAN
        "http://100.124.121.16:8799",     // M4 Tailscale IP
        "http://192.168.0.11:8799",      // M4 Ethernet LAN
        "http://127.0.0.1:8799"          // USB reverse loopback
    };
    private static volatile String activeHost = CANDIDATE_HOSTS[0];

    private TextView titleView;
    private TextView statusView;
    private TextView replyView;
    private Button orbButton;
    private Handler mainHandler;
    private MediaRecorder mediaRecorder;
    private Vibrator vibrator;
    private boolean isRecording = false;
    private File audioFile;

    private void safeVibrate(long ms) {
        try {
            if (vibrator != null) {
                vibrator.vibrate(ms);
            }
        } catch (Throwable ignored) {}
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mainHandler = new Handler(Looper.getMainLooper());
        try {
            vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        } catch (Throwable ignored) {}
        
        try {
            audioFile = new File(getExternalFilesDir(null), "voice_cmd.3gp");
        } catch (Throwable t) {
            audioFile = new File("/sdcard/voice_cmd.3gp");
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#070913"));
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(30, 60, 30, 40);

        titleView = new TextView(this);
        titleView.setText("🚀 JARVIS-OMEGA");
        titleView.setTextColor(Color.parseColor("#00F0FF"));
        titleView.setTextSize(26);
        titleView.setGravity(Gravity.CENTER);
        root.addView(titleView);

        TextView subView = new TextView(this);
        subView.setText("Cockpit Mobile Natif S8 · WiFi & Tailscale");
        subView.setTextColor(Color.parseColor("#8FA0C0"));
        subView.setTextSize(15);
        subView.setGravity(Gravity.CENTER);
        subView.setPadding(0, 5, 0, 30);
        root.addView(subView);

        orbButton = new Button(this);
        orbButton.setText("🎙️\n\nTOUCHEZ POUR PARLER\nou Bouton Volume");
        orbButton.setTextSize(18);
        orbButton.setTextColor(Color.WHITE);
        orbButton.setBackgroundColor(Color.parseColor("#0051FF"));
        LinearLayout.LayoutParams orbParams = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 480);
        orbParams.gravity = Gravity.CENTER;
        orbParams.setMargins(20, 10, 20, 30);
        orbButton.setLayoutParams(orbParams);
        orbButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                toggleRecording();
            }
        });
        root.addView(orbButton);

        statusView = new TextView(this);
        statusView.setText("⚡ Système connecté (WiFi 192.168.0.20)");
        statusView.setTextColor(Color.parseColor("#4ADE80"));
        statusView.setTextSize(16);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 5, 0, 15);
        root.addView(statusView);

        replyView = new TextView(this);
        replyView.setText("Prêt.");
        replyView.setTextColor(Color.WHITE);
        replyView.setTextSize(16);
        replyView.setGravity(Gravity.CENTER);
        replyView.setPadding(20, 15, 20, 25);
        root.addView(replyView);

        LinearLayout quickRow = new LinearLayout(this);
        quickRow.setOrientation(LinearLayout.HORIZONTAL);
        quickRow.setGravity(Gravity.CENTER);
        
        addButton(quickRow, "BILAN", "donne moi le bilan en direct");
        addButton(quickRow, "LINKEDIN", "dernier post linkedin");
        addButton(quickRow, "VENTES", "propositions vente");
        addButton(quickRow, "VOLUME", "augmente le son");
        
        root.addView(quickRow);
        setContentView(root);

        startStatusPolling();
    }

    private void addButton(LinearLayout parent, String label, final String cmd) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextSize(13);
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(Color.parseColor("#1A2744"));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f);
        lp.setMargins(6, 0, 6, 0);
        b.setLayoutParams(lp);
        b.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                sendTextCommand(cmd);
            }
        });
        parent.addView(b);
    }

    private void toggleRecording() {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecordingAndSend();
        }
    }

    private void startRecording() {
        try {
            safeVibrate(50);
            mediaRecorder = new MediaRecorder();
            mediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            mediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.THREE_GPP);
            mediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB);
            mediaRecorder.setOutputFile(audioFile.getAbsolutePath());
            mediaRecorder.prepare();
            mediaRecorder.start();
            isRecording = true;

            orbButton.setText("🛑\n\nÉCOUTE EN COURS...\n(Touchez pour envoyer)");
            orbButton.setBackgroundColor(Color.parseColor("#FF0055"));
            statusView.setText("🎙️ Enregistrement micro actif...");
        } catch (Throwable e) {
            statusView.setText("Micro direct: envoi bilan...");
            isRecording = false;
            sendTextCommand("donne moi le bilan en direct");
        }
    }

    private void stopRecordingAndSend() {
        try {
            if (isRecording && mediaRecorder != null) {
                safeVibrate(100);
                mediaRecorder.stop();
                mediaRecorder.release();
                mediaRecorder = null;
                isRecording = false;

                orbButton.setText("⏳\n\nTRAITEMENT...");
                orbButton.setBackgroundColor(Color.parseColor("#0051FF"));
                statusView.setText("🚀 Envoi au cluster JARVIS...");

                uploadAudio(audioFile);
            }
        } catch (Throwable e) {
            statusView.setText("Arrêt micro...");
            isRecording = false;
            orbButton.setText("🎙️\n\nTOUCHEZ POUR PARLER\nou Bouton Volume");
        }
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_VOLUME_DOWN || keyCode == 220) {
            toggleRecording();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private void uploadAudio(final File file) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                for (String baseHost : CANDIDATE_HOSTS) {
                    try {
                        URL url = new URL(baseHost + "/voice_audio");
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setRequestMethod("POST");
                        conn.setRequestProperty("Content-Type", "application/octet-stream");
                        conn.setDoOutput(true);
                        conn.setConnectTimeout(4000);
                        conn.setReadTimeout(12000);

                        FileInputStream fis = new FileInputStream(file);
                        OutputStream os = conn.getOutputStream();
                        byte[] buffer = new byte[4096];
                        int read;
                        while ((read = fis.read(buffer)) != -1) {
                            os.write(buffer, 0, read);
                        }
                        fis.close();
                        os.close();

                        if (conn.getResponseCode() == 200) {
                            activeHost = baseHost;
                            BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                            StringBuilder sb = new StringBuilder();
                            String line;
                            while ((line = br.readLine()) != null) {
                                sb.append(line);
                            }
                            br.close();

                            JSONObject resp = new JSONObject(sb.toString());
                            final String reply = resp.optString("reply", "Commande traitée.");
                            final String cmd = resp.optString("command", "");

                            mainHandler.post(new Runnable() {
                                @Override
                                public void run() {
                                    replyView.setText(reply);
                                    statusView.setText("✓ " + cmd);
                                    orbButton.setText("🎙️\n\nTOUCHEZ POUR PARLER\nou Bouton Volume");
                                }
                            });
                            return;
                        }
                    } catch (Throwable ignored) {}
                }
                
                mainHandler.post(new Runnable() {
                    @Override
                    public void run() {
                        replyView.setText("Recherche connexion hôte...");
                        statusView.setText("Vérification WiFi/Tailscale...");
                        orbButton.setText("🎙️\n\nTOUCHEZ POUR PARLER\nou Bouton Volume");
                    }
                });
            }
        }).start();
    }

    private void sendTextCommand(final String cmdText) {
        safeVibrate(40);
        statusView.setText("🚀 Envoi: " + cmdText);
        new Thread(new Runnable() {
            @Override
            public void run() {
                for (String baseHost : CANDIDATE_HOSTS) {
                    try {
                        URL url = new URL(baseHost + "/voice");
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setRequestMethod("POST");
                        conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                        conn.setDoOutput(true);
                        conn.setConnectTimeout(3000);
                        conn.setReadTimeout(10000);

                        JSONObject json = new JSONObject();
                        json.put("command", cmdText);
                        OutputStream os = conn.getOutputStream();
                        os.write(json.toString().getBytes("UTF-8"));
                        os.close();

                        if (conn.getResponseCode() == 200) {
                            activeHost = baseHost;
                            BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                            StringBuilder sb = new StringBuilder();
                            String line;
                            while ((line = br.readLine()) != null) {
                                sb.append(line);
                            }
                            br.close();

                            JSONObject resp = new JSONObject(sb.toString());
                            final String reply = resp.optString("reply", "Action exécutée.");

                            mainHandler.post(new Runnable() {
                                @Override
                                public void run() {
                                    replyView.setText(reply);
                                    statusView.setText("✓ Connecté (" + activeHost + ")");
                                }
                            });
                            return;
                        }
                    } catch (Throwable ignored) {}
                }
                
                mainHandler.post(new Runnable() {
                    @Override
                    public void run() {
                        replyView.setText("Erreur réseau: hôte injoignable");
                    }
                });
            }
        }).start();
    }

    private void startStatusPolling() {
        mainHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (!isRecording) {
                    new Thread(new Runnable() {
                        @Override
                        public void run() {
                            for (String baseHost : CANDIDATE_HOSTS) {
                                try {
                                    URL url = new URL(baseHost + "/status");
                                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                                    conn.setConnectTimeout(1500);
                                    conn.setReadTimeout(1500);
                                    if (conn.getResponseCode() == 200) {
                                        activeHost = baseHost;
                                        BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                                        StringBuilder sb = new StringBuilder();
                                        String line;
                                        while ((line = br.readLine()) != null) sb.append(line);
                                        br.close();
                                        final JSONObject obj = new JSONObject(sb.toString());
                                        mainHandler.post(new Runnable() {
                                            @Override
                                            public void run() {
                                                if (!isRecording) {
                                                    statusView.setText("⚡ " + obj.optInt("tasks_count", 0) + " tâches · " + obj.optInt("swarm_runs", 0) + " runs agents");
                                                }
                                            }
                                        });
                                        return;
                                    }
                                } catch (Throwable ignored) {}
                            }
                        }
                    }).start();
                }
                mainHandler.postDelayed(this, 12000);
            }
        }, 2000);
    }

    @Override
    protected void onDestroy() {
        try {
            if (mediaRecorder != null) {
                mediaRecorder.release();
            }
        } catch (Throwable ignored) {}
        super.onDestroy();
    }
}
