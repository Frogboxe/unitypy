using System.Collections;
using System.Collections.Generic;
using IronPython.Hosting;
using UnityEngine;

public class PyServe : MonoBehaviour {

    private dynamic engine;
    private dynamic pyclient;
    private dynamic pyengine;

    void Start(){

        engine = Python.CreateEngine();

        ICollection<string> searchPaths = engine.GetSearchPaths();

        searchPaths.Add(Application.dataPath);
        
        searchPaths.Add(Application.dataPath + @"\Plugins\Lib\");
        engine.SetSearchPaths(searchPaths);

        pyengine = engine.ExecuteFile(Application.dataPath + @"\pyserve27.py");
        pyclient = pyengine.PyClient();
        Debug.Log("Created PyServe");
        Debug.Log("Worked once");

    }

    void Update(){
        object ret = pyclient.remote_call("add", 45, 53);
        if (ret != null){
            Debug.Log((int) ret);
        }
    }

}

