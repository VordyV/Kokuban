namespace speaker;

public static class Protocol {

    public static IEnumerable<Package> Get(Package pkg) {

        if (pkg.Type == PackageType.Request) {

            if (pkg.Header == "ping") yield return Package.CreatePkg(PackageType.Response, "pong", new() {});
            else if (pkg.Header == "showdialog")
            {
                //DialogType type = (DialogType)pkg.Body["type"];
                System.Text.Json.JsonElement jTxt = (System.Text.Json.JsonElement)pkg.Body["txt"];
                string? txt = jTxt.GetString();
                
                System.Text.Json.JsonElement jType = (System.Text.Json.JsonElement)pkg.Body["type"];
                DialogType type = (DialogType)jType.GetInt32();
                
                Main.ShowDialog(type, txt);
            }
            else if (pkg.Header == "showct")
            {
                System.Text.Json.JsonElement jTxt = (System.Text.Json.JsonElement)pkg.Body["txt"];
                string? txt = jTxt.GetString();
                
                System.Text.Json.JsonElement jPrd = (System.Text.Json.JsonElement)pkg.Body["prd"];
                int prd = jPrd.GetInt32();

                TimeSpan period = TimeSpan.FromSeconds(prd);
                
                Main.ShowTextCentral(txt, period);
            }

        }
        
        yield break;
    }
    
    public static Package PkgAuth(string agent, string keyHash) => Package.CreatePkg(PackageType.Request, "auth", new() {{"agent", agent}, {"kh", keyHash}});
    public static Package PkgUpdateProfile(string profile) => Package.CreatePkg(PackageType.Request, "updateprofile", new() {{"profile", profile}});

}