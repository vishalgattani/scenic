# Adding new scenic models from Unity

## 1. Create a new asset bundle

1. Open Unity and assign a new asset bundle name to all the assets you want to bundle.
2. Ensure all the assets have a box collider with the appropriate dimensions since `scenic.configuration_writer` will use these dimensions to generate the model.
3. Create the asset bundle.

## 2. Attach a Unity script to parse the asset bundle

1. Create a new C# script in Unity and name it `GetAssetBundleInformation.cs`.
2. Copy the following code into the script:

```csharp
using UnityEditor;
using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;

using static System.Reflection.BindingFlags;

public class GetAssetBundleInformation : MonoBehaviour {

    [MenuItem ("Assets/Get Asset Bundle Information")]
    static void GetNames ()
    {

        Dictionary<string, string> dic = new Dictionary<string, string>();
        List<List<string>> listofassets = new List<List<string>>();
        string assetBundleDirectory = "Assets/AssetInfo";
        if(!Directory.Exists(assetBundleDirectory))
        {
            FileUtil.DeleteFileOrDirectory(assetBundleDirectory);
            Directory.CreateDirectory(assetBundleDirectory);
        }

        string filename = Application.dataPath+"/AssetInfo/asset_info.csv";

        var names = AssetDatabase.GetAllAssetBundleNames();

        foreach( var assetBundleName in AssetDatabase.GetAllAssetBundleNames() ){
            string assetbundlefile = Application.dataPath+"/AssetInfo/"+assetBundleName+"_asset_info.csv";
            TextWriter fp = new StreamWriter(assetbundlefile,true);
            foreach( var assetPathAndName in AssetDatabase.GetAssetPathsFromAssetBundle(assetBundleName) ){
                // var prefabPath = Path.GetFileNameWithoutExtension(assetPathAndName );
                Debug.Log( assetPathAndName );
                if (assetPathAndName.EndsWith(".prefab")){
                    GameObject loadedPrefab = PrefabUtility.LoadPrefabContents(assetPathAndName);
                    if(loadedPrefab.GetComponent<BoxCollider>() != null){
                        BoxCollider collider = loadedPrefab.GetComponent<BoxCollider>();
                        Debug.Log(assetPathAndName);
                        Debug.Log(collider.bounds.extents.x);
                        string nameWithoutPath = assetPathAndName.Substring( assetPathAndName.LastIndexOf( "/" ) + 1 );
                        string name = nameWithoutPath.Substring( 0, nameWithoutPath.LastIndexOf( "." ) );
                        float x = 2*collider.bounds.extents.x;
                        float y = 2*collider.bounds.extents.y;
                        float z = 2*collider.bounds.extents.z;
                        fp.WriteLine(name+","+assetPathAndName+","+assetBundleName+","+x+","+y+","+z);
                    }
                }
            }
            fp.Close();
        }
    }
}
```
3. From the Editor menu item, click `Assets/Get Asset Bundle Information` to run the script.
4. This generates a CSV file for each asset bundle in the project in the `AssetInfo` folder. The CSV file contains the name of the asset, the path to the asset, and the asset bundle name and the dimensions of the box collider.
5. Copy the CSV file to the `new_bundles` folder.

## 3. Run the Model Creator script

1. Run the `scenic_model_creator.py` script in the `new_bundles` folder.
2. This will generate a `model.scenic` file for each asset bundle in the project and the `asset_info.json` file for each asset bundle.

# Conclusion

Now you have a new model/class definition for each asset in a bundle for `scenic` to generate scenes.