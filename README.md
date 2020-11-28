<p align="center"><img alt="keypirinha-tldr" title="keypirinha-tldr" src="/assets/tldr_banner_readme.png" height="300" /></p>

This is keypirinha-tldr, a [tldr pages](https://tldr.sh) plugin for the
[Keypirinha](http://keypirinha.com) launcher. Now, experience the comfort of navigating console commands in tldr pages right from your favourite launcher. 

<p align="center"><img alt="keypirinha-tldr" title="keypirinha-tldr" src="/assets/screen_clipping.gif" height="400" /></p>

## Install

### Managed

The easiest way is to use the `Install Package` command of  [PackageControl](https://github.com/ueffel/Keypirinha-PackageControl) by [@ueffel](https://github.com/ueffel) (must be installed manually) 

`Install Package "tldr"`

### Manual

* Download `tldr.keypirinha-package` from the [releases](https://github.com/ronan696/keypirinha-tldr/releases) page.
* Copy the file into `Keypirinha\portable\Profile\InstalledPackages` (Portable mode) **OR**<br/>`%APPDATA%\Keypirinha\InstalledPackages` (Installed mode)


## Usage

This plugin adds the following items to the [Catalog](http://keypirinha.com/glossary.html#term-catalog). These items can be accessed by entering any of the keywords in the item name.
- **tldr: Search**

   Select this item to search for a console command in tldr pages. Requires input arguments in the format: <br/>
   `[-p PLATFORM] [-L LANGUAGE] command` <br/>
   - The default platform is **windows**, but can be modified in the plugin [configuration file](/src/tldr.ini). The default platform can be overridden at runtime by using the `-p` option followed by the desired platform. <br/>
   Platforms supported by tldr are **linux**, **windows**, **osx** and **sunos**. <br/>
   If the command does not exist for the desired platform, the tldr page results for the command corresponding to the platform for which it exists, will be shown.
   - The default language is **en**, but can be modified in the plugin [configuration file](/src/tldr.ini). The default language can be overridden at runtime by using the `-L` option followed by the desired language. <br/>
   Languages supported by tldr are **en**, **bs**, **da**, **de**, **es**, **fr**, **hbs**, **hi**, **id**, **it**, **ja**, **ko**, **ml**, **nl**, **no**, **pl**, **pt_BR**, **pt_PT**, **ru**, **sv**, **ta**, **th**, **tr**, **zh**, **zh_TW**. <br/>
   When using the `-L` option, an error will be thrown if the the tldr page for a command does not exist the the desired language.
   

- **tldr: Update Page Cache**

   Select this item to force an update of the local tldr page cache. Local cache will only be maintained for the languages specified in the plugin [configuration file](/src/tldr.ini).
   Please check the configuration file of the plugin for options related to updating local page cache implicitly. <br/>
   _**Note**: Page cache updates may take some time depending on the network connection and system configuration._

Please consult the plugin [configuration file](/src/tldr.ini) for details on all possible configuration options.



## Change Log

### v1.0

* First Release :tada:


## License

This package is distributed under the terms of the [MIT license](/LICENSE).


## Credits

- [@polyvertex](https://github.com/polyvertex), for developing the super fast launcher [Keypirinha](https://keypirinha.com).
- [tldr pages](https://tldr.sh/), for the awesome project.
- [tldr-alfred](https://github.com/cs1707/tldr-alfred) by [@cs1707](https://github.com/cs1707), for the inspiration.


## Contribute

1. Check for open issues or open a fresh issue to start a discussion around a
   feature idea or a bug.
2. Fork this repository on GitHub and start making your changes to a new branch.
3. Send a pull request.

