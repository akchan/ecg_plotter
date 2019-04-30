/*
* Change log
* ==========
* 2019/04/20
*   Created
*/

import java.util.Arrays;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.IOException;


String PI_ADDR = "pi@raspberrypy.local";
String REMOTE_PYTHON_PATH = "/home/pi/.pyenv/shims/python";
String REMOTE_SCRIPT_PATH = "/home/pi/ecg_remote.py";

boolean SAVE_FRAME = false;

float Y_MAG = 0.8;
float SPEED_COEF = 1.0;
int BLACKOUT_WIDTH = 40;
float MIN_VAL_WINDOW = 700;

float[] vals;
int vals_i = 0;
boolean[] vals_flag;
boolean empty_to_render = true;


void setup() {
    size(800, 200);
    background(255);
    frameRate(30);

    int len = int(width / SPEED_COEF);

    vals = new float[len];
    Arrays.fill(vals, 0);

    vals_flag = new boolean[len];
    Arrays.fill(vals_flag, false);

    draw_wait();
    delay(3000);

    thread("watch_val_via_ssh");
}


void draw() {
    background(255);

    // [Debug code]
    // add_rand();

    float[] vals_tmp = vals.clone();
    int vals_i_tmp = vals_i;
    boolean[] vals_flag_tmp = vals_flag.clone();

    textSize(10);
    text("FPS: " + nf(frameRate, 3, 1), 10, 10);

    if (empty_to_render) {
        draw_wait();

        if (SAVE_FRAME) {
            saveFrame("frames/######.png");
        }
        return;
    }

    float[] val_tmp_norm = normalize_vals(vals_tmp, vals_flag_tmp);

    for (int i = 0; i < vals_tmp.length - 1; ++i) {
        boolean to_render = vals_flag_tmp[i] && vals_flag_tmp[i+1];
        if (! to_render) {
            continue;
        }
        float x1 = i * SPEED_COEF;
        float y1 = height - val_tmp_norm[i];

        float x2 = (i+1) * SPEED_COEF;
        float y2 = height - val_tmp_norm[i+1];

        line(x1, y1, x2, y2);
    }
    
    if (SAVE_FRAME) {
        saveFrame("frames/######.png");
    }
}


void draw_wait() {
    fill(0,0,0);
    textSize(32);
    text("Waiting for the ECG monitor data...", 10, 35);
}


void add_val(float val) {
    vals[vals_i] = val;
    vals_flag[vals_i] = true;

    int vals_i_l = (vals_i+BLACKOUT_WIDTH) % vals.length;
    vals_flag[vals_i_l] = false;

    vals_i = (vals_i + 1) % vals.length;

    empty_to_render = false;
}


void add_rand() {
    add_val(random(height));
}


float[] normalize_vals(float[] vals, boolean[] vals_flag) {
    float[] ret = vals.clone();
    FloatList vals_to_render = new FloatList();

    for (int i = 0; i < vals_flag.length; ++i) {
        if (vals_flag[i]) {
            vals_to_render.append(vals[i]);
        }
    }

    float max = vals_to_render.max();
    float min = vals_to_render.min();

    // Add 1 to prevent zero dividing
    float diff = max(max - min, MIN_VAL_WINDOW, 1);

    for (int i = 0; i < ret.length; ++i) {
        ret[i] = (ret[i] - min) / diff * height * Y_MAG + height * (1.0 - Y_MAG) * 0.5;
    }

    return ret;
}


void watch_val_via_ssh() {
    float spf = 0.01; // in millisecond

    try {
        Process process = new ProcessBuilder("ssh", PI_ADDR, REMOTE_PYTHON_PATH + " -u " + REMOTE_SCRIPT_PATH).start();
        InputStreamReader isr = new InputStreamReader(process.getInputStream(), "UTF-8");
        BufferedReader reader = new BufferedReader(isr);
        StringBuilder builder = new StringBuilder();
        String s;

        while (true) {
            while ((s = reader.readLine()) != null) {
                float f = Float.parseFloat(s);
                add_val(f);
            }
            delay(int(spf*1000));
        }
    } catch (IOException e) {
        println("IOException!!");
    }
}
